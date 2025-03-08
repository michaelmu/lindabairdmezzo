import json

from lambda_function import lambda_handler

class Context:
    def __init__(self, arn: str):
        self.invoked_function_arn = arn


if __name__ == "__main__":
    event = {"testmode": "true"}
    response = lambda_handler(event, Context("Sample ARN"))
    print(response)