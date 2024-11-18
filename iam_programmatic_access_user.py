# Format:
# 1. List IAM Users
# 2. Access their Access key created dates
# 3. Compare today's date with created dates
# 4. Filter which users are not resetting their access keys every 25 days
# 5. We need to make a report as a CSV file
# 6. In the beginning of every month, this script should run automatically
# 7. Report should be sent via email to the team DL


import boto3
from datetime import date, datetime, timedelta, timezone
#import pytz
import csv
import os
from botocore.exceptions import ClientError
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def age_of_access_keys(writer):
    #1. List IAM Users
    iam_users = boto3.client('iam')
    list_of_users = iam_users.list_users()

    empty_iam_report = {}
    #print(list_of_users['Users'])

    # 2. Access their Access key created dates
    for user in list_of_users['Users']:
        actual_usernames = user['UserName']
        #print(actual_usernames)

        list_access_keys = iam_users.list_access_keys( UserName=actual_usernames)
        #print(list_access_keys['AccessKeyMetadata'])
        for access_key in list_access_keys['AccessKeyMetadata']:
            iam_users_created_date = access_key['CreateDate']
            #current_date_utc = datetime.now(pytz.utc)

            current_date_utc = datetime.now(timezone.utc)

            # Converting to local time zone (e.g., Eastern Time)
            #local_timezone = pytz.timezone('US/Eastern')
            #current_date_local = current_date_utc.astimezone(local_timezone)

            #print("Current date and time in UTC:", current_date_utc)
            #print("Current date and time in local time zone:", current_date_local)


    # 3. Compare today's date with created dates
            #key_age = (current_date_local-iam_users_created_date).days
            key_age = (current_date_utc-iam_users_created_date).days
            #print(actual_usernames, key_age)

    # 4. Filter which users are not resetting their access keys every 25 days
            if(key_age >= 25):
                print(actual_usernames, key_age)
                empty_iam_report["user_name"] = actual_usernames
                empty_iam_report["age_of_key"] = key_age
                empty_iam_report["created_date"] = iam_users_created_date
                writer.writerow(empty_iam_report)

def send_report_to_emails(file_name):
        # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "emmanueljunior9@yahoo.com"

    # Replace recipient@example.com with a "To" address. If your account 
    # is still in the sandbox, this address must be verified.
    RECIPIENT = "emmanueljunior9@yahoo.com"

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the 
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    #CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-west-2"

    # The subject line for the email.
    SUBJECT = "Data for AccessKeys older than 25 days"

    # The full path to the file that will be attached to the email.
    ATTACHMENT = file_name

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = "Hello,\r\nPlease see the attached file for a list of customers to contact."

    # The HTML body of the email.
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <h1>Hello Everyone!</h1>
    <p>Please see the attached file for a list of AccessKeys which were created over 25 days ago.</p>
    </body>
    </html>
    """

    # The character encoding for the email.
    CHARSET = "utf-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses', region_name=AWS_REGION)

    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT 
    msg['From'] = SENDER 
    msg['To'] = RECIPIENT

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Encode the text and HTML content and set the character encoding. This step is
    # necessary if you're sending a message with characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)

    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)

    # Define the attachment part and encode it using MIMEApplication.
    att = MIMEApplication(open(ATTACHMENT, 'rb').read())

    # Add a header to tell the email client to treat this part as an attachment,
    # and to give the attachment a name.
    att.add_header('Content-Disposition','attachment',filename=os.path.basename(ATTACHMENT))

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    # Add the attachment to the parent container.
    msg.attach(att)
    #print(msg)
    try:
        #Provide the contents of the email.
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=[
                RECIPIENT
            ],
            RawMessage={
                'Data':msg.as_string(),
            },
            #ConfigurationSetName=CONFIGURATION_SET
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent Successfully! with Message ID:"),
        print(response['MessageId'])


def lambda_handler(event, context):
    field_names = ["user_name","age_of_key","created_date"]
    file_name = "/tmp/IAM_Users_Report.csv"
    with open (file_name, "w", newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        
        age_of_access_keys(writer)
    send_report_to_emails(file_name)
