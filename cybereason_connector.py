# File: cybereason_connector.py
# Edited by Billy Giang
# --
# -----------------------------------------
# Phantom Cybereason Connector
# -----------------------------------------

# Phantom App imports
import phantom.app as phantom
from cybereason_main import cybereason_client

from phantom.base_connector import BaseConnector
from phantom.action_result import ActionResult

# Imports local to this App
# from cybereason_consts import *

import simplejson as json
import datetime


def _json_fallback(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    else:
        return obj


# Define the App Class
class CybereasonConnector(BaseConnector):

    ACTION_ID_TEST_ASSET_CONNECTIVITY = "test_asset_connectivity"
    ACTION_ID_GET_INDICATORS = "get_indicators"
    ACTION_ID_ADD_INDICATORS = "add_indicators"
    ACTION_ID_REMOVE_INDICATORS = "remove_indicators"

    def __init__(self):
        # Call the BaseConnectors init first
        super(CybereasonConnector, self).__init__()

    def login(self):
        config = self.get_config()

        # Getting all elements and assigning them to variables
        server_address = str(config.get("server_address"))
        port = str(config.get("port"))
        protocol = str(config.get("protocol"))
        username = str(config.get("username"))
        password = str(config.get("password"))
        proxy = str(config.get("proxy"))

        # Confirming progress on screen
        self.save_progress("Server address: " + server_address)
        self.save_progress("Port: " + port)
        self.save_progress("Protocol: " + protocol)
        self.save_progress("Proxy: " + proxy)

        client = cybereason_client(
                                  server_address=server_address,
                                  port=port,
                                  protocol=protocol,
                                  username=username,
                                  password=password,
                                  proxy=proxy,
                                 )

        self.save_progress("Testing Login Connection...")
        try:
            client.login()
            msg = "Successful Connection."
        except:
            msg = "Connection Failed."

        return msg, client

    def _test_connectivity(self, param):
        try:
            msg, client = self.login()
        except:
            self.save_progress("There has been an issue")
        return self.set_status_save_progress(phantom.APP_SUCCESS, msg)

    def _handle_getIndicators(self, param):

        self.debug_print("param", param)

        # Add an action result to the App Run
        action_result = ActionResult(dict(param))
        self.add_action_result(action_result)

        try:
            # Attempt to log into server
            self.save_progress("Logging in...")
            msg, client = self.login()
            cybereason_data = client.getIndicators()
        except:
            action_result.set_status(phantom.APP_ERROR, "Error")
            return action_result.get_status()
        # The data is returned in a list format, so
        # this extracts the data from the list, and formats it into a
        # dictionary object where it can be added to the "action_result" object
        for i in cybereason_data:
            i = json.dumps(i, default=_json_fallback)
            i = json.loads(i)
            action_result.add_data(i)
        # set_status updates the current status and outputs to "message"
        action_result.set_status(phantom.APP_SUCCESS, "Successfully grabbed data.")
        return action_result.get_status()

    def _handle_updateIndicators(self, param, choice):
        key = str(param['key'])
        reputation = str(param['reputation'])
        prevention = str(param['prevention'])
        comment = "null"

        action_result = ActionResult(dict(param))
        self.add_action_result(action_result)

        try:
            # Attempt to log into server
            msg, client = self.login()
        except:
            action_result.set_status(phantom.APP_ERROR, "Unable to login.")

        # Formatting the data
        if choice:
            # REMOVING
            remove = 'true'
        else:
            # ADDING
            remove = 'false'
        prevention = prevention.lower()
        remove = remove.lower()

        # Setting up to add the the table widget, must in a list, and must contain dictionary
        tempObj = [{'key': key, 'reputation': reputation, 'prevention': prevention, 'comment': comment}]

        # Adding to object to action result so it can be read into the table
        for i in tempObj:
            i = json.dumps(i, default=_json_fallback)
            i = json.loads(i)
            action_result.add_data(i)
            
        try:
            # Updating the cybereason client
            client.updateIndicators(key, reputation, prevention, remove)
            action_result.set_status(phantom.APP_SUCCESS, "Successful")
        except:
            action_result.set_status(phantom.APP_ERROR, "Error with updateIndicator function")
            return action_result.get_status()
        return action_result.get_status()

    def handle_action(self, param):

        # Added the action to execute the handle updateIndicators
        ret_val = phantom.APP_SUCCESS

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if (action_id == self.ACTION_ID_GET_INDICATORS):
            ret_val = self._handle_getIndicators(param)
        elif (action_id == phantom.ACTION_ID_TEST_ASSET_CONNECTIVITY):
            ret_val = self._test_connectivity(param)
        elif (action_id == self.ACTION_ID_ADD_INDICATORS):
            ret_val = self._handle_updateIndicators(param, False)
        elif (action_id == self.ACTION_ID_REMOVE_INDICATORS):
            ret_val = self._handle_updateIndicators(param, True)

        return ret_val


if __name__ == '__main__':
    import sys
    import pudb
    pudb.set_trace()

    if (len(sys.argv) < 2):
        print "No test json specified as input"
        exit(0)

    with open(sys.argv[1]) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = CybereasonConnector()
        connector.print_progress_message = True
        ret_val = connector._handle_action(json.dumps(in_json), None)
        print (json.dumps(json.loads(ret_val), indent=4))

    exit(0)
