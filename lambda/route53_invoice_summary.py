import boto3
import gzip
import csv
import io
import os
import re
from datetime import datetime, timedelta

# ========== Configuration ==========
S3_BUCKET = "my-route53-billing-main"
REPORT_PREFIX = "billing/my-cur-report"
SUMMARY_PREFIX = "route53_invoice_summary"
SNS_TOPIC_ARN = "arn:aws:sns:ap-southeast-1:886679765175:route53-billing-report"

s3 = boto3.client('s3')
sns = boto3.client('sns')

def lambda_handler(event, context):
    today = datetime.utcnow()
    start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    end_date = today.replace(day=1)
    billing_period = f"{start_date.strftime('%Y%m01')}-{end_date.strftime('%Y%m01')}"
    month_str = start_date.strftime('%B-%Y').lower()
    output_file = f"route53_invoice_summary_{month_str}.csv"
    s3_prefix = f"{REPORT_PREFIX}/{billing_period}/"

    print(f"Looking for CUR report in: s3://{S3_BUCKET}/{s3_prefix}")
    report_key = get_latest_csv_gz_key(s3_prefix)
    if not report_key:
        print(f"No report found for period: {billing_period}")
        return

    print(f"Found report: {report_key}")
    gz_filename = os.path.basename(report_key)
    backup_key = f"resources_invoice_summary/resources-report-gz/resources_invoice_summary_{month_str}.csv.gz"
    cur_gz_data = s3.get_object(Bucket=S3_BUCKET, Key=report_key)['Body'].read()
    s3.put_object(Bucket=S3_BUCKET, Key=backup_key, Body=cur_gz_data)
    print(f"Backup copy uploaded to s3://{S3_BUCKET}/{backup_key}")

    with gzip.GzipFile(fileobj=io.BytesIO(cur_gz_data)) as gz:
        csv_reader = csv.reader(io.TextIOWrapper(gz, encoding='utf-8'))
        header = next(csv_reader, None)
        output = [["InvoiceID", "Operation", "DomainName", "PurchaseDate", "Cost"]]
        report_year = today.strftime('%Y')
        report_month = start_date.strftime('%m')

        for row in csv_reader:
            if len(row) < 28:
                continue
            operation = row[15].lower()
            if 'renewdomain' in operation or 'registerdomain' in operation:
                invoice = row[2] if row[2] else "inv-ongoing"
                cost = "{:.2f}".format(float(row[24]) if row[24] else 0.0)
                desc = row[26]
                domain = "N/A"
                m = re.search(r"(?:[Rr]enewal|[Rr]egistration) of ([a-zA-Z0-9.-]+)", desc)
                if m:
                    domain = m.group(1)
                try:
                    usage_start = datetime.strptime(row[12][:10], "%Y-%m-%d")
                    adjusted_date = usage_start - timedelta(days=4)
                    purchase_date = f"{report_year}-{report_month}-{adjusted_date.strftime('%d')}"
                except:
                    purchase_date = "N/A"
                output.append([invoice, operation.upper(), domain, purchase_date, cost])

    if len(output) == 1:
        msg = f"Route53 billing summary for {month_str} is empty."
        send_sns(f"Route53 - No Registration or Renewal Found - {month_str}", msg)
        print("No records found, summary skipped.")
        return

    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    csv_writer.writerows(output)
    csv_body = csv_buffer.getvalue()
    s3_key = f"{SUMMARY_PREFIX}/{output_file}"
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=csv_body)
    print(f"Uploaded summary to s3://{S3_BUCKET}/{s3_key}")

    preview = "\n".join([",".join(row) for row in output[:6]])
    message = f"""Route53 billing summary for {month_str} is available
S3 URL: s3://{S3_BUCKET}/{s3_key}

{output_file}
-------------------------------------
{preview}"""
    send_sns(f"Route53 Billing Summary - {month_str}", message)
    print("SNS notification sent.")

def get_latest_csv_gz_key(prefix):
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)
    latest_key = None
    for page in pages:
        for obj in sorted(page.get('Contents', []), key=lambda x: x['LastModified']):
            if obj['Key'].endswith('.csv.gz'):
                latest_key = obj['Key']
    return latest_key

def send_sns(subject, message):
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject,
        Message=message
    )
