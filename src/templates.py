class SlackTemplateBuilder:

    def __init__(self, payload):
        self.title = payload.get("title")
        self.description = payload.get("description")
        self.severity_type = payload.get("severity_type")
        self.compliance = payload.get("compliance")
        self.resource_type = payload.get("resource_type")
        self.resource_items = payload.get("resource_items")

    def build_template(self):
        template = []
        title = self.build_title()
        resource_details = self.build_resource_details()

        resource_list = []
        for item in self.resource_items:
            apply_val = "apply-" + item.get("id")
            not_apply_val = "not-apply-" + item.get("id")
            resource_list.append(self.build_resource_item(item.get("name"), apply_val, not_apply_val))

        button = self.build_approve_button()

        template.append(title)
        template.append(resource_details)
        template.append(self.build_divider())
        template.extend(resource_list)
        template.append(self.build_divider())
        template.append(button)
        return {"blocks": template}

    @staticmethod
    def build_divider():
        return {
            "type": "divider"
        }

    def build_title(self):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Title*:\n*<fakeLink.toEmployeeProfile.com| {self.title}>*"
            }
        }

    def build_resource_details(self):
        return {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{self.description}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Severity:*\n{self.severity_type}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Compliance:*\n{self.compliance}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Resource Type:*\n{self.resource_type}"
                }
            ]
        }

    @staticmethod
    def build_resource_list_title():
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Resources*:"
            }
        }

    @staticmethod
    def build_resource_item(resource_item_name, apply_val, not_apply_val):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{resource_item_name}"
            },
            "accessory": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "emoji": True,
                    "text": "Select"
                },
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Apply"
                        },
                        "value": apply_val
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Not Apply"
                        },
                        "value": not_apply_val
                    }
                ]
            }
        }

    @staticmethod
    def build_approve_button():
        return {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Approve"
                    },
                    "style": "primary",
                    "value": "approve"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Cancel"
                    },
                    "style": "danger",
                    "value": "cancel"
                }
            ]
        }
