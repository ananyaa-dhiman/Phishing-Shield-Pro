"""
make_train_data.py
One time helper script. Builds a synthetic csv file of phishing and
legit looking email text so the ML classifier has something to learn
from out of the box. Run this once before train_model.py if
train_data.csv does not already exist.

In a real company you would replace this csv with real labeled email
samples, this is just so the app works right after install.
"""

import csv
import random
import config

random.seed(42)

phishing_subjects = [
    "Urgent: Verify your account now",
    "Your account has been suspended",
    "Action required: Update your billing information",
    "Security Alert: unusual sign in activity detected",
    "Final notice: invoice overdue, pay immediately",
    "You have won a prize, claim now",
    "Confirm your password within 24 hours",
    "Your package could not be delivered, click to reschedule",
    "IT Support: your mailbox is full, click here",
    "Tax refund pending, verify your identity",
    "Dear customer, your account will be closed",
    "Re: Wire transfer request, please action urgently",
    "Your Netflix payment failed, update card details",
    "Apple ID locked, verify now to restore access",
    "HR Notice: update your direct deposit information",
]

phishing_bodies = [
    "Dear customer, we noticed unusual activity on your account. Click here to verify your identity immediately or your account will be suspended within 24 hours.",
    "Your account has been limited. To restore full access please confirm your password and billing details by clicking the secure link below.",
    "This is your final notice. Your invoice is overdue. Please make payment immediately using the gift card codes listed below to avoid legal action.",
    "Congratulations, you have been selected to receive a prize. Claim your reward now by entering your bank account number and social security number.",
    "Kindly revert with your login credentials so we can do the needful and restore your mailbox access before it expires.",
    "We detected a sign in attempt from an unknown device. If this was not you, verify your identity now or your account will be permanently closed.",
    "Please find attached invoice. Wire transfer must be completed within 24 hours to avoid penalty fees. Use bitcoin for faster processing.",
    "Your package delivery failed. Click here to reschedule and confirm your payment information to release the parcel from customs.",
    "Act now, this offer expires soon. Update your billing information by clicking the link to avoid service suspension.",
    "Dear valued customer, your password will expire today. Click here immediately to reset your password and avoid losing access.",
]

legit_subjects = [
    "Team meeting moved to 3pm tomorrow",
    "Project status update for this week",
    "Lunch this Friday?",
    "Quarterly report draft attached",
    "Reminder: submit timesheet by end of day",
    "Notes from today's standup",
    "Welcome to the team",
    "Conference room booking confirmation",
    "Your order has shipped",
    "Newsletter: company updates for June",
    "Feedback on the design document",
    "Schedule for next week's training session",
    "Updated travel itinerary",
    "Thanks for your help yesterday",
    "Question about the budget spreadsheet",
]

legit_bodies = [
    "Hi team, just a quick note that our meeting tomorrow has moved to 3pm in the main conference room. See you there.",
    "Hi, attached is the draft of the quarterly report. Let me know if you have any comments before Friday.",
    "Hey, are you free for lunch this Friday? Thinking about trying the new place down the street.",
    "Reminder to submit your timesheet by end of day today so payroll can process everything on time.",
    "Here are the notes from today's standup. Please review and let me know if I missed anything important.",
    "Welcome to the team, we are excited to have you. Your laptop and accounts should be set up by Monday.",
    "Your order has shipped and should arrive within 3 to 5 business days. Thanks for your purchase.",
    "Attached is the updated travel itinerary for next week's conference. Let me know if anything needs to change.",
    "Thanks again for your help yesterday, it really made a difference for the launch.",
    "Quick question on the budget spreadsheet, can you confirm the numbers in row 12 before we send it out.",
]


def build_dataset():
    rows = []

    for i in range(120):
        subject = random.choice(phishing_subjects)
        body = random.choice(phishing_bodies)
        text = subject + " " + body
        rows.append((text, "phishing"))

    for i in range(120):
        subject = random.choice(legit_subjects)
        body = random.choice(legit_bodies)
        text = subject + " " + body
        rows.append((text, "legit"))

    random.shuffle(rows)

    with open(config.TRAIN_DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        for text, label in rows:
            writer.writerow([text, label])

    print("wrote", len(rows), "rows to", config.TRAIN_DATA_FILE)


if __name__ == "__main__":
    build_dataset()
