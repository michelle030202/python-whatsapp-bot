from flask import current_app, jsonify
import json
import requests
import re
import logging

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def generate_response(message_body, yes_counter=0, previous_question=None):
    message_body = message_body.strip()

    if "hi" in message_body or "Hi" in message_body or "Hey" in message_body:
        return "Hi, I am a bot that will help you journal and track your habits. Respond with 'Damnnn' when you're ready to start setup."

    elif ("damnnn" in message_body.lower() or "Damnnn" in message_body or "damn" in message_body.lower() or
          "Damn" in message_body or "damnn" in message_body.lower() or "Damnn" in message_body or
          "Damnnnn" in message_body or "damnnnn" in message_body.lower()):
        return "Just kidding, you could've written whatever, but don't tell anyone, it'll be our secret 😉, so how should I call you? (what's your name that is)"

    elif "ron" in message_body.lower():
        name = message_body[0].upper() + message_body[1:]
        return f"Cool {name}, so let me tell you about myself. I'm a very cool bot that will help you journal and track your habits. Basically, I will be your friend that also helps you track your habits and journal your life. I'm here to help you be the best version of yourself :)\n\nLet's get to know each other! How old are you?"


    elif message_body.isdigit():
        age = int(message_body)
        return f"Cool, I'm 24. Where are you from?"

    elif "israel" in message_body or "Israel" in message_body:
        location = message_body
        return f"Nice, I know some people from {location}. I'm from the cloud though. What do you like to do in your free time?"

    elif "dancing" in message_body or "Dancing" in message_body or "dancing and going to the beach" in message_body or "goind to beach" in message_body or "Dancing and going to the beach" in message_body:
        return "Wow, sounds fun! Now let's get to what you came here for. Would you like to set your first habit to track?"


    elif "Yes" in message_body:
        return "Ok, so let's set it up. \n\nDo you have a habit in mind that you'd like to track?"

    elif "Yeah" in message_body or "yeah" in message_body:
        return "That's great! So tell me, what's the habit you want to track?"


    elif "I want" in message_body or "i want" in message_body:
        previous_question = "remind"
        return "Great, so now that we have our habit and goal, it's important to set reminders and time for the habit \n\n I can send you a message everytime you need to complete a habit, and I'll track their completion either if you tell me when you're done or from your journal entries \n\nThe best way to do your habits consistently is to put them in your schedule, Would you like me to remind you? (yes/no)"

    elif "yes" in message_body:
        return "Awesome, so I'll remind you today."

    else:
        return "I'm not sure how to respond to that. Can you please try rephrasing?"


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"
    whatsapp_style_text = re.sub(pattern, replacement, text)
    return whatsapp_style_text


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    response = generate_response(message_body)

    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)

    data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
    send_message(data)


def is_valid_whatsapp_message(body):
    return (
            body.get("object")
            and body.get("entry")
            and body["entry"][0].get("changes")
            and body["entry"][0]["changes"][0].get("value")
            and body["entry"][0]["changes"][0]["value"].get("messages")
            and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
