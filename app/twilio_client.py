import os

from twilio.rest import Client


class TwilioClient:
    def __init__(self):
        self.client = Client(
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"],
        )

        self.from_number = os.environ["TWILIO_FROM_NUMBER"]
        self.to_number = os.environ["TWILIO_TO_NUMBER"]

    def send_sms(self, body):
        message = self.client.messages.create(
            body=body,
            from_=self.from_number,
            to=self.to_number,
        )

        return message.sid