# Automated IAM Access Key Report
# Overview
This project automates the generation and delivery of a monthly report that lists IAM users whose access keys are older than 25 days. The report is generated using an AWS Lambda function running Python 3.12 and the boto3 library, and is sent via email to the designated distribution list (DL) team members.

# Features
Lists all IAM users.
Accesses their access key creation dates.
Compares today's date with the creation dates.
Filters users whose access keys are not reset every 25 days.
Generates a report in CSV format.
Automatically runs on the first of every month using a CRON job with a CRON expression.
Sends the report via email to the team.

# Requirements
AWS account with necessary IAM and SES permissions.
Verified email address in SES.
Boto3 library installed.
Python 3.12 runtime for the Lambda function.

# Setup
1. Create and Configure AWS Lambda Function
Create a Lambda function with the Python 3.12 runtime.
Attach a role with necessary IAM and SES permissions to the Lambda function.
2. Create and Verify SES Identity
Verify the sender email address in Amazon SES.
3. Define the CRON Expression
Use a CRON expression to schedule the Lambda function to run on the first of every month:

cron(0 0 1 * ? *)

# Package and Deploy the Code
Package the code and dependencies into a ZIP file.
Upload the ZIP file to the AWS Lambda console.

# Python Script
import boto3
from datetime import datetime, timezone
import csv
import os
from botocore.exceptions import ClientError
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def age_of_access_keys(writer):
    # 1. List IAM Users
    iam_users = boto3.client('iam')
    list_of_users = iam_users.list_users()
    empty_iam_report = {}

    # 2. Access their Access key created dates
    for user in list_of_users['Users']:
        actual_usernames = user['UserName']
        list_access_keys = iam_users.list_access_keys(UserName=actual_usernames)
        for access_key in list_access_keys['AccessKeyMetadata']:
            iam_users_created_date = access_key['CreateDate']
            current_date_utc = datetime.now(timezone.utc)

            # 3. Compare today's date with created dates
            key_age = (current_date_utc - iam_users_created_date).days

            # 4. Filter which users are not resetting their access keys every 25 days
            if key_age >= 25:
                empty_iam_report["user_name"] = actual_usernames
                empty_iam_report["age_of_key"] = key_age
                empty_iam_report["created_date"] = iam_users_created_date
                writer.writerow(empty_iam_report)

def send_report_to_emails(file_name):
    SENDER = "emmanueljunior9@yahoo.com"
    RECIPIENT = "emmanueljunior9@yahoo.com"
    SUBJECT = "Data for AccessKeys older than 25 days"
    ATTACHMENT = file_name
    BODY_HTML = """
    <html>
    <head></head>
    <body>
    <h1>Hello Everyone!</h1>
    <p>Please see the attached file for a list of AccessKeys which were created over 25 days ago.</p>
    </body>
    </html>
    """
    CHARSET = "utf-8"
    client = boto3.client('ses', region_name="us-west-2")
    msg = MIMEMultipart('mixed')
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = RECIPIENT

    msg_body = MIMEMultipart('alternative')
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    msg_body.attach(htmlpart)

    att = MIMEApplication(open(ATTACHMENT, 'rb').read())
    att.add_header('Content-Disposition', 'attachment', filename=os.path.basename(ATTACHMENT))

    msg.attach(msg_body)
    msg.attach(att)

    try:
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=[RECIPIENT],
            RawMessage={'Data': msg.as_string()}
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent Successfully! with Message ID:", response['MessageId'])

def lambda_handler(event, context):
    field_names = ["user_name", "age_of_key", "created_date"]
    file_name = "/tmp/IAM_Users_Report.csv"
    with open(file_name, "w", newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=field_names)
        writer.writeheader()
        age_of_access_keys(writer)
    send_report_to_emails(file_name)

# License
This project is licensed under the MIT License. See the LICENSE file for more details.
