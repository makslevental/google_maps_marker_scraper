from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import *
from pyvirtualdisplay import Display
import sys
from proxy2 import test, ProxyRequestHandler
import config
from multiprocessing import Process
import time
import re

class MyProxyRequestHandler(ProxyRequestHandler):
    def response_handler(self, req, req_body, res, res_body):
        if 'maps/api/js?' in req.raw_requestline:

            marker_constructor_name = re.search(r'Marker:([^,]+),', res_body)
            if marker_constructor_name is not None:
                # _.ue=function(a){this.__gm={set:null,me:null};qe.call(this,a)};
                pat = r"""%s=function\(a\){
                                this.([^=]+)={
                                    ([^:]+):null,
                                    ([^:]+):null
                                };
                                ([^.]+).call\(this,a\)
                            };""".replace('\n','').replace(' ','') % marker_constructor_name.group(1)
                marker_constructor = re.search(pat, res_body)
                assert marker_constructor, 'maps has changed'
                sub = r"""
                            %s=function(a){
                                if("position" in a){
                                    window.maxs_markers_latlng.push([a.position.lat(),a.position.lng()])
                                }
                                this.\g<1>={
                                    \g<2>:null,
                                    \g<3>:null
                                };
                                \g<4>.call(this,a);
                                window.maxs_markers.push(this)
                            };
                        """ % marker_constructor_name.group(1)
                new_res_body, number_of_subs_made = re.subn(pat,sub, res_body,1)
                assert number_of_subs_made == 1, 'maps has changed'
            else:
                raise Exception('maps has changed')

            pat = r'_\.([a-z]+)\.set=function\(a,b\){'
            sub = r"""
                    _.\g<1>.set=function(a,b){
                        if(a=="content" && "anchor" in this){
                            window.maxs_markers_infowindow.push([this.anchor.position.toString(),b])
                        };
                        if(a=="anchor" && "content" in this){
                            window.maxs_markers_infowindow.push([b.position.toString(),this.content])
                        };
                    """
            setter = re.search(pat, new_res_body)
            if setter is not None:
                new_res_body, number_of_subs_made = re.subn(pat,sub,new_res_body,1)
                assert number_of_subs_made == 1, "maps has changed"
            else:
                raise Exception('maps has changed')
            return 'window.maxs_markers=[];window.maxs_markers_latlng=[];window.maxs_markers_infowindow=[];'+new_res_body

    def print_info(self, req, req_body, res, res_body):
        pass

def run_proxy():
    sys.argv = ['','']
    sys.argv[1] = config.PROXY_PORT
    test(HandlerClass=MyProxyRequestHandler)

def scrape(url):
    proc1 = Process(target=run_proxy)
    proc1.start()
    display = Display(visible=0, size=(800, 600))
    display.start()
    try:
        # chrome_option = webdriver.ChromeOptions()
        # chrome_option.add_argument("--proxy-server=127.0.0.1:{}".format(config.PROXY_PORT))
        # capabilities = DesiredCapabilities.CHROME
        # capabilities['loggingPrefs'] = {'browser': 'ALL'}
        # driver = webdriver.Chrome(chrome_options=chrome_option, desired_capabilities=capabilities)

        proxy = Proxy({
            'proxyType': ProxyType.MANUAL,
            'httpProxy': '127.0.0.1:{}'.format(config.PROXY_PORT),
            'ftpProxy': '127.0.0.1:{}'.format(config.PROXY_PORT),
            'sslProxy': '127.0.0.1:{}'.format(config.PROXY_PORT),
            'noProxy': ''  # set this value as desired
        })
        driver = webdriver.Firefox(proxy=proxy)

        for i in range(1):
            driver.get(url)
            time.sleep(config.WAIT_LOAD)
            driver.execute_script("""for (var i = 0; i<window.maxs_markers.length;i++) {
                                        google.maps.event.trigger(window.maxs_markers[i],'click')
                                    }"""
                                  )
            markers = driver.execute_script('return window.maxs_markers_infowindow')
            print driver.execute_script('return window.maxs_markers_latlng')
            if len(markers):
                break
        else:
            for entry in driver.get_log('browser'):
                print entry
            raise Exception("didn't work")


        return markers
    finally:
        display.stop()
        proc1.terminate()


if __name__ == '__main__':
    url = 'http://www.atwoods.com/LocationEventMapping.aspx'
    # url = 'http://www.berryplastics.com/about-us/locations'
    url = 'https://www.lkqpickyourpart.com/locations'
    # url = 'http://www.rubytuesday.com/locations'
    print scrape(url)
