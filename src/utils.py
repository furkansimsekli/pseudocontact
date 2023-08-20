def create_result_message(contacts: list[tuple]) -> str:
    message = ""

    for i, contact in enumerate(contacts):
        message += (f"<b>Name:</b> {contact[2]}\n"
                    f"<b>Number:</b> {contact[3]}\n\n")

        if i != len(contacts) - 1:
            message += f"--------\n\n"

    return message
