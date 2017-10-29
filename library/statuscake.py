import requests
import json
from ansible.module_utils.basic import *

class StatusCake:
    URL_UPDATE_TEST = "https://app.statuscake.com/API/Tests/Update"
    URL_ALL_TESTS = "https://app.statuscake.com/API/Tests"
    URL_DETAILS_TEST = "https://app.statuscake.com/API/Tests/Details"

    def __init__(self, module, username, api_key, name, url, state, test_tags, check_rate, test_type, contact_group, paused, node_locations, confirmation, timeout, status_codes, host, custom_header, follow_redirect, enable_ssl, find_string, do_not_find):
        self.headers = {"Username": username, "API": api_key}
        self.module = module
        self.name = name
        self.url = url
        self.state = state
        self.test_tags = test_tags
        self.test_type = test_type
        self.contact_group = contact_group
        self.paused = paused
        self.node_locations = node_locations
        self.confirmation = confirmation
        self.timeout = timeout
        self.status_codes = status_codes
        self.host = host
        self.custom_header = custom_header
        self.follow_redirect = follow_redirect
        self.enable_ssl = enable_ssl
        self.find_string = find_string
        self.do_not_find = do_not_find

        if self.custom_header:
            data['CustomHeader'] = self.custom_header.replace("'", "\"")

        if not check_rate:
            self.check_rate = 300
        else:
            self.check_rate = check_rate

        if not test_type:
            self.test_type = "HTTP"
        else:
            self.test_type = test_type

        self.data = {"WebsiteName": self.name,
                "WebsiteURL": self.url,
                "CheckRate": self.check_rate,
                "TestType": self.test_type,
                "TestTags": self.test_tags,
                "ContactGroup": self.contact_group,
                "Paused": self.paused,
                "NodeLocations": self.node_locations,
                "Confirmation": self.confirmation,
                "Timeout": self.timeout,
                "StatusCodes": self.status_codes,
                "WebsiteHost": self.host,
                "FollowRedirect": self.follow_redirect,
                "EnableSSLWarning": self.enable_ssl,
                "FindString": self.find_string,
                "DoNotFind": self.do_not_find,
                }

        self.result = {
            'changed': False,
            'name': self.name,
            'state': self.state,
            'response': "",
            'diff': {
                'before': {},
                'after': {}
            }
        }

    def check_response(self,response):
        self.result['response'] = response['Message']
        if response['Success']:
            self.result['changed'] = True
            
    def check_test(self):
        response = requests.get(self.URL_ALL_TESTS, headers=self.headers)
        json_resp = response.json()

        for item in json_resp:
            if item['WebsiteName'] == self.name:
                return item['TestID']

    def delete_test(self):
        test_id = self.check_test()

        if not test_id:
            self.result['response'] = "This Check doesn't exists"
        else:
            data = {'TestID': test_id}
            if self.module.check_mode:
                self.result['changed'] = True
                self.result['response'] = "This Check Has Been Deleted. It can not be recovered."
            else:
                response = requests.delete(self.URL_DETAILS_TEST, headers=self.headers,data=data)
                self.check_response(response.json())
                    
    def create_test(self):

        test_id = self.check_test()
        
        if not test_id:
            if self.module.check_mode:
                self.result['changed'] = True
                self.result['response'] = "Test inserted"
            else:
                response = requests.put(self.URL_UPDATE_TEST, headers=self.headers, data=self.data)
                self.check_response(response.json())
            self.result['diff']['after'] = self.data
        else:
            self.data['TestID'] = test_id
            url_details_test = self.URL_DETAILS_TEST + "/?TestID=" + str(test_id)
            response = requests.get(url_details_test, headers=self.headers)
            req_data = self.convert(response.json())
            diffkeys = [k for k in self.data if self.data[k] and str(self.data[k]) != str(req_data[k])]
            if self.module.check_mode:
                if len(diffkeys) != 0:
                    self.result['changed'] = True
                    self.result['response'] = "Test updated"
                else:
                    self.result['response'] = "No data has been updated (is any data different?) Given: "+str(test_id)
            else:
                response = requests.put(self.URL_UPDATE_TEST, headers=self.headers, data=self.data)
                self.check_response(response.json())
            self.result['diff']['before'] = {k: req_data[k] for k in diffkeys}
            self.result['diff']['after'] = {k: self.data[k] for k in diffkeys}

    # convert data returned by request to a similar and comparable estruture
    def convert(self,req_data):
        req_data['WebsiteURL'] = req_data.pop('URI')
        req_data['TestTags'] = req_data.pop('Tags')
        req_data = {k: req_data[k] for k in req_data.keys() if k in self.data.keys()}
        for key in req_data.keys():
            if  type(req_data[key]) is list:
                req_data[key] = [item.encode('UTF8') for item in req_data[key]]
                req_data[key] = ','.join(req_data[key])
            if  type(req_data[key]) is unicode:
                req_data[key] = req_data[key].encode('UTF-8')
            if req_data[key] is True:
                req_data[key] = 1
            if req_data[key] is False:
                req_data[key] = 0
        return req_data

    def get_result(self):
        result = self.result
        return result

def run_module():

    module_args = dict(
        username=dict(type='str', required=True),
        api_key=dict(type='str', required=True),
        name=dict(type='str', required=True),
        url=dict(type='str', required=True),
        state = dict(default='present', choices=['absent', 'present']),
        test_tags=dict(type='str', required=False),
        check_rate=dict(type='int', required=False),
        test_type=dict(type='str', required=False),
        contact_group=dict(type='int', required=False),
        paused=dict(type='int', required=False),
        node_locations=dict(type='str', required=False),
        confirmation=dict(type='int', required=False),
        timeout=dict(type='int', required=False),
        status_codes=dict(type='str', required=False),
        host=dict(type='str', required=False),
        custom_header=dict(type='str', required=False),
        follow_redirect=dict(type='int', required=False),
        enable_ssl=dict(type='int', required=False),
        find_string=dict(type='str', required=False),
        do_not_find=dict(type='int', required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    username = module.params['username']
    api_key = module.params['api_key']
    name = module.params['name']
    url = module.params['url']
    state = module.params['state']
    test_tags = module.params['test_tags']
    check_rate = module.params['check_rate']
    test_type = module.params['test_type']
    contact_group = module.params['contact_group']
    paused = module.params['paused']
    node_locations = module.params['node_locations']
    confirmation = module.params['confirmation']
    timeout = module.params['timeout']
    status_codes = module.params['status_codes']
    host = module.params['host']
    custom_header = module.params['custom_header']
    follow_redirect = module.params['follow_redirect']
    enable_ssl = module.params['enable_ssl']
    find_string = module.params['find_string']
    do_not_find = module.params['do_not_find']

    test = StatusCake(module, username, api_key, name, url, state, test_tags, check_rate, test_type, contact_group, paused, node_locations, confirmation, timeout, status_codes, host, custom_header, follow_redirect, enable_ssl, find_string, do_not_find)

    if state == "absent":
        test.delete_test()
    else:
        test.create_test()

    result = test.get_result()
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':  
    main()
