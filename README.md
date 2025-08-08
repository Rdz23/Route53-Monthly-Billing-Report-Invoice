# 🧾 AWS Route53 Monthly Billing Report with Invoice

Automated reporting and notification system to track AWS Route 53 domain registration and renewal activities, along with associated **Invoice IDs**, based on the AWS **Cost and Usage Report (CUR)**.

---

## 📄 Description

This solution automatically processes the AWS CUR file to extract domain registration and renewal transactions from AWS Route 53, identifies the corresponding Invoice IDs, and sends out a formatted report via **SNS Notification**.

It is ideal for teams that want monthly visibility into Route 53 domain billing, especially for:

- **Tracking domain renewals**
- **Confirming invoiced transactions**
- **Monitoring domain-related costs**

### 🔍 Current Problem

If you're managing **multiple domains**—each owned by **different departments or clients**—it's often difficult to split the billing per domain.  
The default AWS Billing dashboard doesn't break down Route 53 costs with enough granularity.

This automation helps by:

- **Identifying each domain's renewal or registration entry**
- **Mapping the cost to the corresponding Invoice ID**
- **Allowing you to chargeback or cross-charge by domain owner**

It gives you a **quick monthly summary** of all active domain transactions at a glance.

---

## ⏰ Report Schedule

- **Every 5th day of the month**
- **Time:** 07:00 UTC (15:00 PHT)
- **Trigger:** AWS EventBridge
- **Runtime:** AWS Lambda (Python)

---

## 📦 Repository Structure

```bash
.
├── lambda/
│   ├── route53_invoice_summary.py   # Main Lambda function
│   └── requirements.txt             # Optional: for local testing
├── eventbridge/
│   └── route53-monthly-schedule.json  # EventBridge cron rule
├── samples/
│   ├── route53_invoice_summary_June-2025.csv  # Sample CSV report
│   └── sns_notification_preview.txt           # SNS notification sample
├── README.md
