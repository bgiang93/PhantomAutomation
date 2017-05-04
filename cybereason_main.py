# import base64
import csv
# import io
import json
import logging
# import os
from urlparse import urlunsplit, urljoin
import requests

logger = logging.getLogger('main_logger')


class LoginError(Exception):
    pass


class LogoutError(Exception):
    pass


class cybereason_client(object):
    def __init__(self, server_address='sce-ui.cybereason.net', port='443', protocol='https', username='user', password='password', cert=False, proxy={}):
        logger.info('Initializing the Cybereason REST client API.')
        self.cr_address = str(server_address)
        self.cr_port = str(port)
        self.cr_protocol = str(protocol)
        self.cr_base_url = urlunsplit((self.cr_protocol, self.cr_address + ':' + self.cr_port, '', '', ''))
        self.cr_rest_url = urljoin(self.cr_base_url, 'rest/')
        self.cr_rest_classification_url = urljoin(self.cr_rest_url, r'classification/')
        self.username = username
        self.password = password
        self.certificate = cert
        self.proxies = {'http': proxy,
                        'https': proxy,
                        }
        self.session = requests.session()

    def login(self):
        '''
        Description: Login to Cybereason REST using a username and password.
        Example POST Request: https://HX_IP_address:port_number/login.html
        Required header:
                Authorization: Basic "username:password"
        Params: None
        Fail Condition: Not 204 response.
        Return: Token used for subsequent requests.
        '''
        logger.debug('Logging into Cybereason as %s', self.username)
        request_url = urljoin(self.cr_base_url, 'login.html')
        data = {
                'username': self.username,
                'password': self.password,
               }
        response = self.session.post(request_url, proxies=self.proxies, data=data, verify=self.certificate)
        self.auth_cookie = None
        for cookie in self.session.cookies:
            if cookie.name == "JSESSIONID" and cookie.value:
                self.auth_cookie = cookie
        if not (response.status_code == 200 and self.auth_cookie):
            logger.error('Login Failed. Response code: ' + str(response.status_code))
            raise LoginError('Login Failed. Response code: ' + str(response.status_code))

    def updateIndicators(self, values, malicious_type='blacklist', prevent='false', remove='false'):
        '''
        Description: Get indicator list from Cybereason
        Example POST Request: https://XXX

        Fail Condition: 1. Status Code NOT 200
        Params: None
        Return: None.
        '''
        logger.debug('Updating indicators')

        if not isinstance(values, list):
            values = [values]
        headers = {
                   'Content-Type': 'application/json',
                  }
        data = [
                {
                    "keys": values,
                    "maliciousType": malicious_type,
                    "prevent": prevent,
                    "remove": remove,
                }
               ]
        request_url = urljoin(self.cr_rest_classification_url, 'update')
        data = json.dumps(data)
        response = self.session.post(request_url, headers=headers, data=data, proxies=self.proxies)

        try:
            json_resp = response.json()
        except:
            json_resp = {}

        if not (response.status_code == 200 and json_resp.get('outcome', None) == 'success'):
            raise Exception('Update indicators failed. Response code: ' + str(response.status_code))
        try:
            reader_list = csv.DictReader(response.content.splitlines())
        except:
            return []
        return list(reader_list)

    def getIndicators(self):
        '''
        Description: Get indicator list from Cybereason
        Example GET Request: https://172.20.17.98:3000/rest/download
        Required header:
        X-FeApi-Token: token
        Fail Condition: 1. Status Code NOT 200
        Params: None
        Return: None.
        '''
        logger.debug('Pulling indicators')

        request_url = urljoin(self.cr_rest_classification_url, 'download')
        response = self.session.get(request_url, proxies=self.proxies)

        if response.status_code != 200:
            raise Exception('Pull indicators failed. Response code: ' + str(response.status_code))
        try:
            reader_list = csv.DictReader(response.content.splitlines())
        except:
            return []

        return list(reader_list)
