from controller.Bot import Bot
import argparse
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Main',
                                        prog="TEST",
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    argparser.add_argument('-m', dest='mode', help='Mode', metavar='', default=None, type=str)
    argparser.add_argument('-c', '--config', help='Config', metavar='', default='config.conf', type=str)
    argparser.add_argument('-id', '--id', help='ID', metavar='', default=None, type=str)
    args = argparser.parse_args()

    bot = Bot(config_file=args.config)

    if args.mode == "start":
        print "--STARTING BOT--"
        print
        bot_account = bot.get_bot(user_id=args.id).fetchone
        print "Bot Loaded"
        print
        if bot_account:
            driver = webdriver.PhantomJS(
                executable_path="C:\phantomjs-1.9.8-windows\phantomjs.exe"
            )
            driver.wait = WebDriverWait(driver, 2)

            try:
                driver.get("http://mbasic.facebook.com")
                print "Facebook Loaded"
                print
                WebDriverWait(driver, 10).until(EC.title_contains("Facebook"))
                email = driver.find_element_by_name('email')
                password = driver.find_element_by_name('pass')
                email.send_keys(bot_account['username'])
                password.send_keys(bot_account['password'])
                print "Typing username and password..."
                password.submit()
                WebDriverWait(driver, 10).until(EC.title_contains("Facebook"))
                print "Logged in"
                while (True):
                    driver.get('https://mbasic.facebook.com/home.php?sk=h_chr')
                    like_btn = driver.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Suka')]")))
                    like_btn.click()
                    current_date = datetime.now()
                    print "[{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}] Liked".format(current_date.year, current_date.month,
                                                                                 current_date.day, current_date.hour,
                                                                                 current_date.minute, current_date.second)
                    time.sleep(10)

            except Exception as e:
                print e
            finally:
                driver.quit()
    elif args.mode == "bot_list":
        print "--BOT LIST--"
        print
        bot_account = bot.get_bot(user_id=args.id).fetchall
        for v in bot_account:
            print "ID: {}".format(v['id'])
            print "Name: {}".format(v['name'])
            print "Username: {}".format(v['username'])
            print
    else:
        pass