# -*- coding: utf-8
from configparser import ConfigParser
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from argparse import ArgumentParser
from webdriver_manager.chrome import ChromeDriverManager
import re
from urllib.parse import quote
from urllib import request
import os
import sys
import time
import warnings
import json
import threading
import datetime
warnings.filterwarnings('ignore')

def dropdown_handler(driver, xpath: str):
    """
    点击带有滚动条的菜单
    ref: https://stackoverflow.com/questions/57303355
    """
    wait = WebDriverWait(driver, 10)
    ele = wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
    ele.location_once_scrolled_into_view
    ele.click()
    time.sleep(0.1)


def login(driver, userName, password, retry=0):
    if retry == 3:
        raise Exception('Portal login failure')

    print('Portal login...',flush=True)

    appID = 'portal2017'
    iaaaUrl = 'https://iaaa.pku.edu.cn/iaaa/oauth.jsp'
    appName = quote('北京大学校内信息门户新版')
    redirectUrl = 'https://portal.pku.edu.cn/portal2017/ssoLogin.do'

    driver.get('https://portal.pku.edu.cn/portal2017/')
    driver.get(
        f'{iaaaUrl}?appID={appID}&appName={appName}&redirectUrl={redirectUrl}')
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, 'logon_button')))
    driver.find_element_by_id('user_name').send_keys(userName)
    time.sleep(0.1)
    driver.find_element_by_id('password').send_keys(password)
    time.sleep(0.1)
    driver.find_element_by_id('logon_button').click()
    try:
        WebDriverWait(driver,
                      10).until(EC.visibility_of_element_located((By.ID, 'all')))
        print('Portal Login successful！',flush=True)
    except:
        print('Try again...',flush=True)
        login(driver, userName, password, retry + 1)


# 智慧场馆
def go_to_simso(driver):
    button = driver.find_element_by_id('all')
    driver.execute_script("$(arguments[0]).click()", button)
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, 'venues')))
    driver.find_element_by_id('venues').click()
    time.sleep(0.3)
    driver.switch_to.window(driver.window_handles[-1])
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[3]/div/div[3]/div[1]/div[1]')))


# 场地预约
def go_to_application_out(driver):
    go_to_simso(driver)
    driver.find_element_by_xpath('/html/body/div[1]/div/div/div[3]/div/div[3]/div[1]/div[1]').click()
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'venueDetailBottomItem')))


# 等待12:00预订时间
def wait(driver, booktime):
    timeArray_new = time.strptime(booktime, "%Y-%m-%d %H:%M:%S")
    timeStamp_new = int(time.mktime(timeArray_new))
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    timeArray_now = time.strptime(now, "%Y-%m-%d %H:%M:%S")
    timeStamp_now = int(time.mktime(timeArray_now))
    time_delay = timeStamp_new - timeStamp_now
    m = int((time_delay%(60*60*24))%(60*60)/60)
    s = int((time_delay%(60*60*24))%(60*60)%60)
    print(str(m*60+s)+'seconds until the venue opens for booking',flush=True)
    time.sleep(m*60+s+1.5)
    driver.refresh()
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/form/div/div/div/div[1]/div/div/input')))


# 邱德拔/五四羽毛球场
def fill_out(driver, space):
    driver.find_elements_by_class_name('venueDetailBottomItem')[space].click()
    print('Enter the field',flush=True)


# 刷新页面选择日期
def fill_in(driver):
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[3]/div[1]/div/div/div/div/div/table/tbody/tr[1]/td[2]/div')))
    driver.find_element_by_xpath('/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[3]/div[1]/div/div/div/div/div/table/tbody/tr[1]/td[2]/div').click()
    # 已阅读并同意
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[4]/label')))
    driver.find_element_by_xpath('/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[4]/label').click()
    # 点击日期
    date = driver.find_element_by_xpath('/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/form/div/div/div/div[1]/div/div/input')
    driver.execute_script("arguments[0].click();", date)
    WebDriverWait(driver,5).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'ivu-date-picker-cells-cell')))

# 选择日期
def date(driver, day):
    # 确认日期
    print('Confirmation date',flush=True)
    txt = "//em[text()='{}']".format(day)
    driver.find_element_by_xpath(txt).click()
    WebDriverWait(driver,5).until(
        EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[3]/div[1]/div/div/div/div/div/table/tbody')))
        
# 找场地
def choose1(driver, time): #-2,-3
    print('Confirming the site',flush=True)
    parent = driver.find_element_by_xpath("/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[3]/div[1]/div/div/div/div/div/table/tbody")
    WebDriverWait(driver,5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '.reserveBlock.position.free')))
    child = parent.find_elements_by_tag_name('tr')
    choose2(driver, child, time)


# 确认场地
def choose2(driver, child, time):
    for i in time:
        child[i].find_elements_by_css_selector('.reserveBlock.position.free')[0].click()
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[5]/div/div[2]')))

# 我要预约
def book(driver):
    print('To make an appointment',flush=True)
    driver.find_element_by_xpath('/html/body/div[1]/div/div/div[3]/div[2]/div/div[2]/div[5]/div/div[2]').click()
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, '//div[@class="payHandleItem "]')))

# 提交订单
def submit(driver):
    print('In order submission',flush=True)
    time.sleep(0.1)
    driver.find_elements_by_xpath('//div[@class="payHandleItem "]')[0].click()
    time.sleep(2)
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/div/div/div[3]/div[2]/div/div[3]/div[7]/div[2]/button')))

# 支付
def pay(driver):
    print('In the payment',flush=True)
    driver.find_element_by_xpath('/html/body/div[1]/div/div/div[3]/div[2]/div/div[3]/div[7]/div[2]/button').click()
    time.sleep(1)
    print('Site paid',flush=True)


def run(driver, userName, password, space, day, time, booktime):

    for try_times in range(10):
        t = []
        try:
            print("======= The", try_times + 1, "time try =======")
            t.append(threading.Thread(target=login(driver, userName, password)))
            t.append(threading.Thread(target=go_to_application_out(driver)))
            t.append(threading.Thread(target=fill_out(driver, space)))
            t.append(threading.Thread(target=wait(driver, booktime)))
            t.append(threading.Thread(target=fill_in(driver)))
            t.append(threading.Thread(target=date(driver, day)))
            t.append(threading.Thread(target=choose1(driver, time)))
            t.append(threading.Thread(target=book(driver)))
            t.append(threading.Thread(target=submit(driver)))
            #t.append(threading.Thread(target=pay(driver)))
            for tt in t:
                tt.start()
                tt.join()
            break

        except Exception as e:
            #print(e,flush=True)
            print("Booking error",flush=True)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--userName', type=str)
    parser.add_argument('--passWord', type=str)
    parser.add_argument('--space', type=str)
    parser.add_argument('--day', type=str)
    parser.add_argument('--time', type=str)
    parser.add_argument('--booktime', type=str)
    args = parser.parse_args()

    #chrome_options = Options()
    #chrome_options.add_argument("--headless")
    '''
    driver_pjs = webdriver.Edge(
        options=chrome_options,
        executable_path='/usr/bin/chromedriver',
        service_args=['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1'])
    '''
    driver_pjs = webdriver.Chrome(ChromeDriverManager().install())
    print('Browser started',flush=True)
    
    timel = args.time.split()
    run(driver_pjs, args.userName, args.passWord, int(args.space), int(args.day), [int(x) for x in timel], args.booktime)

    driver_pjs.quit()
