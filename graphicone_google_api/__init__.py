import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

CREDENTIALS_DATA = {'type': 'service_account',
                    'project_id': os.environ['G_CREDS_PROJECT_ID'],
                    'private_key_id': os.environ['G_CREDS_PRIVATE_KEY_ID'],
                    'private_key': os.environ['G_CREDS_PRIVATE_KEY'],
                    'client_email': os.environ['G_CREDS_CLIENT_EMAIL'],
                    'client_id': os.environ['G_CREDS_CLIENT_ID'],
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
                    'client_x509_cert_url': os.environ['G_CREDS_CLIENT_CERT_URL']}


class GoogleSpreadsheet:

    def __init__(self, spreadsheet_id, google_auth_file_path):

        self.__spreadsheetId = spreadsheet_id

        credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_auth_file_path,
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/drive'])

        http_auth = credentials.authorize(httplib2.Http())
        self.__service = apiclient.discovery.build('sheets', 'v4', http=http_auth)

    def get_all_spreadsheet_values(self, cell_range="A1:E999999"):

        """Return all values from spreadsheet in format of:
            [
                ['Email', 'Username', 'Name'],
                ['test1@mail.com', 'TEST1', 'TEST NAME1'],
                ['test2@mail.com', 'TEST2', 'TEST NAME2']
            ]
        """

        results = self.__service.spreadsheets().values().batchGet(spreadsheetId=self.__spreadsheetId,
                                                                  ranges=[cell_range],
                                                                  valueRenderOption='FORMATTED_VALUE',
                                                                  dateTimeRenderOption='FORMATTED_STRING').execute()

        return results['valueRanges'][0]['values']

    def delete_line_and_up_others(self, row_num):
        """Delete row from spreadsheet with specified number and move up other lines"""

        batch_update_spreadsheet_request_body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "dimension": "ROWS",
                            "sheetId": 0,
                            "startIndex": row_num - 1,
                            "endIndex": row_num
                        }
                    }
                }
            ]
        }

        self.__service.spreadsheets().batchUpdate(spreadsheetId=self.__spreadsheetId,
                                                  body=batch_update_spreadsheet_request_body).execute()

    def append_new_line_in_spreadsheet(self, values):

        """Insert new line in the end of filled lines in spreadsheet. Values should be in format of:

            ["test1@mail.com", "TEST1", "TEST NAME1"]
        """

        last_not_empty_line_num = len(self.get_all_spreadsheet_values())

        self.__service.spreadsheets().values().append(spreadsheetId=self.__spreadsheetId,
                                                      range='A' + str(last_not_empty_line_num + 1),
                                                      valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
                                                      body={"values": [values]}).execute()

    def delete_row_with_value_included(self, value, returning=False):
        """Delete all rows where passed value detected between row items"""

        all_spreadsheet_values = self.get_all_spreadsheet_values()

        counter = 1
        for line in all_spreadsheet_values:
            if value in line:
                self.delete_line_and_up_others(counter)
                if returning:
                    return line
                counter -= 1
            counter += 1


def add_email_for_subscription(cur, account_queries, excel, email='', username='', name='', day='FRI',
                               insert_timestamp=datetime.now(), app_patch=False):
    """Updating users email subscription info"""

    if username:
        excel.delete_row_with_value_included(username)

    raw_query = account_queries.get_basic_user_info_by_email_or_username(email=email, username=username)
    cur.execute(raw_query)
    result = cur.fetchone()

    if result:
        username, name, email = result

    if app_patch:
        raw_query = account_queries.update_email_notification_settings(enable=True, username=username,
                                                                       push_notification_day='FRI')
        cur.execute(raw_query)

    excel.append_new_line_in_spreadsheet([email, username, name, day, insert_timestamp.strftime('%Y-%m-%d %H-%M-%S')])


def update_subscribed_email(excel, username, email=None, new_day=None):
    """Change email in google spreadsheet file"""

    deleted_item = excel.delete_row_with_value_included(username, True)
    if deleted_item:
        if email:
            deleted_item[0] = email
        if new_day:
            deleted_item[-2] = new_day

        excel.append_new_line_in_spreadsheet(deleted_item)


def update_info_on_registration(excel, username, email, name):
    """Update info in google spreadsheet if user with this email already subscribed on email"""

    google_spreadsheet_item = excel.delete_row_with_value_included(email, True)

    if google_spreadsheet_item:
        excel.append_new_line_in_spreadsheet([email, username, name, 'FRI', google_spreadsheet_item[-1]])
        return True
    else:
        return False
