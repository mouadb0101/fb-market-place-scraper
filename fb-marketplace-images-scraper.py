import argparse, os, time, wget, json, piexif, ssl, urllib
from selenium import webdriver, common
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions
from datetime import datetime
import threading

login = False
def start_session(username, password):
    global login
    print("Opening Browser...")
    wd_options = Options()
    wd_options.add_argument("--disable-notifications")
    wd_options.add_argument("--disable-infobars")
    wd_options.add_argument("--mute-audio")
    # wd_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(chrome_options=wd_options)
    driver.maximize_window()
    '''driver.set_network_conditions(
        offline=False,
        latency=5,  # additional latency (ms)
        download_throughput=500 * 1024,  # maximal throughput
        upload_throughput=500 * 1024)'''

    # Login
    driver.get("https://www.facebook.com/")
    if username != "":
        print("Logging In...")

        email_id = driver.find_element_by_id("email")
        pass_id = driver.find_element_by_id("pass")
        email_id.send_keys(username)
        pass_id.send_keys(password)
        driver.find_element_by_id("loginbutton").click()
        login = True

    return driver


total_scrolls = 10
current_scrolls = 0
scroll_time = 5
old_height = 0


def check_height():
    new_height = driver.execute_script("return document.body.scrollHeight")
    return new_height != old_height


def scroll():
    global old_height
    current_scrolls = 0

    while True:
        try:
            if current_scrolls == total_scrolls:
                return

            old_height = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, scroll_time, 0.05).until(lambda driver: check_height())
            current_scrolls += 1
        except TimeoutException:
            break

    return


def download_photos(location, category):
    global login
    # Set waits (go higher if slow internet)
    wait = WebDriverWait(driver, 30)
    main_wait = 1
    stuck_wait = 3

    # Nav to photos in marketplace
    print("Navigating to marketplace...")
    photos_url = 'https://www.facebook.com/marketplace/{}/{}/?exact=false'.format(location, category)
    print(photos_url)
    driver.get(photos_url)
    print("Downloading Images...")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "a75w6hnp")))
    i = 0
    # Prep structure
    data = {'tagged': []}
    while i < 1000:
        time.sleep(main_wait)
        elem = driver.find_elements_by_css_selector(".a75w6hnp")[i]
        try:
            elem.find_elements_by_tag_name("a")[0].click()
            i += 1
        except WebDriverException:
            scroll()
            continue

        # Get user information
        if login:
            try:
                user = wait.until(EC.presence_of_element_located((By.XPATH,
                                                                  '//div[@class="nks5qztm"]//span[@class="gvxzyvdx '
                                                                  'aeinzg81 t7p7dqev gh25dzvf exr7barw k1z55t6l '
                                                                  'oog5qr5w innypi6y pbevjfx6"]')))
                print(user.text)
            except exceptions.StaleElementReferenceException:
                pass


        try:
            # Download multi-images
            wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="fsf7x5fv jvc6uz2b g90fjkqk"]')))
            elems = driver.find_elements_by_css_selector(".fsf7x5fv.jvc6uz2b.g90fjkqk")
            for e in elems:
                try:
                    # Get image url
                    element = e.find_element_by_tag_name("img")
                    media_url = element.get_attribute('src')
                except exceptions.StaleElementReferenceException:
                    continue

                doc = {
                    'fb_url': driver.current_url,
                    'fb_date': datetime.now(),
                    # 'fb_caption': ,
                    'media_url': media_url,
                    'media_type': 'image',
                    'user_name': user.text if login else "",
                    # 'user_url': ,
                    # 'user_id':
                }

                # Get Deets & move on
                print("%s)" % (len(data['tagged']) + 1))
                data['tagged'].append(doc)

                # For slow internet: download without indexing
                threading.Thread(target=download_image, args=(doc, (len(data['tagged']) + 1),)).start()
        except TimeoutException:
            # Only one Image found
            element = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//span[@class='alzwoclg b0ur3jhr']//img")))
            media_url = element.get_attribute('src')
            doc = {
                'fb_url': driver.current_url,
                'fb_date': datetime.now(),
                # 'fb_caption': ,
                'media_url': media_url,
                'media_type': 'image',
                'user_name': user.text if login else "",
                # 'user_url': ,
                # 'user_id':
            }

            # Get Deets & move on
            print("%s)" % (len(data['tagged']) + 1))
            data['tagged'].append(doc)

            # For slow internet: download without indexing
            threading.Thread(target=download_image, args=(doc, (len(data['tagged']) + 1),)).start()

        print("-" * 20 + "Done Indexing Photos: %s" % driver.current_url)
        elem1 = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='om3e55n1 cgu29s5g "
                                                                     "alzwoclg i85zmo3j']//div["
                                                                     "@role='button']")))
        elem1.click()
    # Save JSON deets
    with open('tagged.json', 'w') as f:
        json.dump(data, f, indent=4)
    f.close()


def download_image(doc, i):
    folder = 'photos/'
    if doc['media_type'] == 'image':
        # Save new file
        filename_date = datetime.today().strftime('%Y-%m-%d')
        img_id = doc['media_url'].split('_')[1]
        new_filename = folder + filename_date + '_' + img_id + '.jpg'
        if os.path.exists(new_filename):
            print("Already Exists (Skipping): %s" % new_filename)
        else:
            delay = 1
            while True:
                try:
                    print("Downloading " + doc['media_url'])
                    img_file = wget.download(doc['media_url'], new_filename, False)
                    break
                except (TimeoutError, urllib.error.URLError) as e:
                    print("Sleeping for {} seconds".format(delay))
                    time.sleep(delay)
                    delay *= 2
            # Update EXIF Date Created
            exif_dict = piexif.load(img_file)
            exif_date = datetime.today().strftime("%Y:%m:%d %H:%M:%S")

            img_desc = doc['fb_url'].split("&")[0]
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = exif_date
            exif_dict['0th'][piexif.ImageIFD.Copyright] = doc['user_name'].encode('utf-8') if login else ""
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = img_desc.encode('utf-8')
            piexif.insert(piexif.dump(exif_dict), img_file)
            print(str(i + 1) + ') Added ' + new_filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Facebook Scraper')
    parser.add_argument('-u', type=str, default='', help='FB Username')
    parser.add_argument('-p', type=str, default='', help='FB Password')
    parser.add_argument('-l', type=str, default='algiers', help='Marketplace Location')
    parser.add_argument('-c', type=str, default='vehicles', help='Marketplace Category')
    args = parser.parse_args()
    try:
        # if not (args.u and args.p):
        # print('Please try again with FB credentials (use -u -p)')
        # else:
        driver = start_session(args.u, args.p)
        download_photos(args.l, args.c)
    except KeyboardInterrupt:
        print(
            '\nThanks for using the script! Please raise any issues at: https://github.com/mouadb0101/fb-market-place-scraper/issues/new')
        pass
