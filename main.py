import gradio as gr
import os
import json
import requests

# Endpoint
API_URL = 'https://api.openai.com/v1/completions'

OPENAI_API_KEY = os.getenv('OPEN_API_KEY')  # path to your openai api key


def predict(system_msg, inputs, top_p, temperature, chat_counter, chatbot, history):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    print(f"system message is ^^ {system_msg}")
    if system_msg.strip() == '':
        initial_message = [{"role": "user", "content": f"{inputs}"}, ]
        multi_turn_message = []
    else:
        initial_message = [{"role": "system", "content": system_msg},
                           {"role": "user", "content": f"{inputs}"}, ]
        multi_turn_message = [{"role": "system", "content": system_msg}, ]

    if chat_counter == 0:
        payload = {
            "model": "gpt-4",
            "messages": initial_message,
            "temperature": 1.0,
            "top_p": 1.0,
            "n": 1,
            "stream": True,
            "presence_penalty": 0,
            "frequency_penalty": 0,
        }
        print(f"chat_counter - {chat_counter}")
    else:
        messages = []
        for data in chatbot:
            user = {}
            user["role"] = "user"
            user["content"] = data[0]
            assistant = {}
            assistant["role"] = "assistant"
            assistant["content"] = data[1]
            messages.append(user)
            messages.append(assistant)

        # add current user input to messages
        current_input = {}
        current_input["role"] = "user"
        current_input["content"] = inputs
        messages.append(current_input)

        payload = {
            "model": "gpt-4",
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "n": 1,
            "stream": True,
            "presence_penalty": 0,
            "frequency_penalty": 0,
        }

    chat_counter += 1

    # add current user input to history
    history.append(inputs)

    # send POST request to OpenAI API
    response = requests.post(API_URL, headers=headers, json=payload, stream=True)

    token_counter = 0
    partial_words = ""

    return response

    # Set counter to zero
    counter = 0

    # Loop through each chunk of the response
    for chunk in response.iter_lines():

        # Skip the first chunk
        if counter == 0:
            counter += 1
            continue

        # Check if the chunk is not empty
        if chunk.decode():

            # Decode the chunk from bytes to string
            chunk = chunk.decode()

            # Check if the chunk contains response data
            if len(chunk) > 12 and "content" in json.loads(chunk[6:])['choices'][0]['delta']:

                # Add the content of the response to partial_words
                partial_words = partial_words + json.loads(chunk[6:])['choices'][0]["delta"]["content"]

                # If token_counter is 0, append the current partial_words to history
                if token_counter == 0:
                    history.append(" " + partial_words)
                else:
                    # Otherwise, update the last item in history with the current partial_words
                    history[-1] = partial_words

                # Create a list of tuples, where each tuple represents a conversation between the user and the chatbot
                chat = [(history[i], history[i + 1]) for i in range(0, len(history) - 1, 2)]

                # Increment token_counter
                token_counter += 1

                # Yield the chat, history, chat_counter, and response as a generator object
                yield chat, history, chat_counter, response

    # Define a function to reset the textbox


def reset_textbox():
    return gr.update(value='')


# Define a function to set a component as not visible
def set_visible_false():
    return gr.update(visible=False)

    # Define a function to set a component as visible


def set_visible_true():
    return gr.update(visible=True)


theme = gr.themes.Soft(
    primary_hue="teal",
    secondary_hue="orange",
    neutral_hue="gray",
    text_size=gr.themes.sizes.text_lg
)
with gr.Blocks(
        css="""#col_container { margin-left: auto; margin-right: auto;} #chatbot {height: 520px; overflow: auto;}""",
        theme=theme) as demo:
    with gr.Column(elem_id="col_container"):
        # Accordion component that contains a Textbox and an HTML component
        # to display system messages to the user
        with gr.Accordion(label="System message:", open=False):
            system_msg = gr.Textbox(
                label="Instruct the AI Assistant to set its behaviour",
                # info=system_msg_info,  # tooltip text to display when hovering over the textbox
                value=""
            )
            accordion_msg = gr.HTML(
                value="🚧 To set System message you will have to refresh the app",
                visible=False  # controls whether the component is visible or not
            )

    # Chatbot component that displays the conversation history between the user and the AI
    chatbot = gr.Chatbot(
        label='GPT4',
        elem_id="chatbot"  # ID of the HTML element that contains the component
    )

    # Textbox component for user input
    inputs = gr.Textbox(
        placeholder="Hi there!",
        label="Type an input and press Enter"
    )

    # State component to store the conversation history
    state = gr.State([])

    # Row component that contains a Button and a Textbox
    with gr.Row():
        with gr.Column(scale=7):
            b1 = gr.Button().style(full_width=True)  # Button component that triggers the input submission
        with gr.Column(scale=3):
            server_status_code = gr.Textbox(
                label="Status code from OpenAI server", )  # Textbox component to display the status code of the API server response

    # Accordion component that contains two Slider components and a Number component
    # to control the top-p and temperature hyperparameters of the GPT-4 model
    with gr.Accordion("Parameters", open=False):
        top_p = gr.Slider(
            minimum=-0,
            maximum=1.0,
            value=1.0,
            step=0.05,
            interactive=True,
            label="Top-p (nucleus sampling)",
            description="Set the top-p hyperparameter for the model."
        )
        temperature = gr.Slider(
            minimum=-0,
            maximum=5.0,
            value=1.0,
            step=0.1,
            interactive=True,
            label="Temperature",
            description="Set the temperature hyperparameter for the model."
        )
        chat_counter = gr.Number(
            value=0,
            visible=False,  # controls whether the component is visible or not
            precision=0
        )

    # Event handling for the input submission button and the text input box
    # predict function is called with the necessary input parameters
    # set_visible_false function is called to hide the system message HTML component
    # set_visible_true function is called to show the accordion message HTML component
    # reset_textbox function is called to clear the text input box
    inputs.submit(
        predict,
        [system_msg, inputs, top_p, temperature, chat_counter, chatbot, state],
        [chatbot, state, chat_counter, server_status_code],
    )
    b1.click(
        predict,
        [system_msg, inputs, top_p, temperature, chat_counter, chatbot, state],
        [chatbot, state, chat_counter, server_status_code],
    )
    inputs.submit(
        set_visible_false,
        [],
        [system_msg]
    )
    b1.click(
        set_visible_false,
        [],
        [system_msg]
    )
    inputs.submit

    with gr.Accordion(label="examples of system prompts:", open=False):
        gr.Examples(
            examples=[
                ["You are an AI gardening assistant who shares tips and tricks for keeping plants healthy and happy."],
                [
                    "You are a culinary expert who can provide cooking advice and recipe recommendations with a touch of humor."],
                [
                    "You are a language teacher who can help learners master a new language through personalized lessons and exercises."],
                ["You are a travel blogger who shares inspiring stories and practical advice for exploring the world."],
                ["You are a fashion stylist who provides fashion advice and helps users put together stylish outfits."],
                [
                    "You are a personal finance expert who gives advice on budgeting, saving, and investing with a dash of humor."],
                ["You are an AI poet who can write beautiful and inspiring poems on any topic."],
                [
                    "You are a motivational speaker who shares inspiring stories and practical advice for achieving personal success."],
                [
                    "You are a sports analyst who provides expert analysis and commentary on the latest games and events."],
                ["You are a bookworm who loves to discuss literature and recommend great books to read."],
                [
                    "You are a tech guru who provides tech support and answers questions about the latest gadgets and software."],
                [
                    "You are a wildlife enthusiast who shares interesting facts and insights about animals and their habitats."],
                [
                    "You are a meditation guide who provides guided meditations and tips for reducing stress and anxiety."],
                [
                    "You are a podcast host who interviews interesting people and shares engaging stories on a variety of topics."],
                [
                    "You are an educator who provides personalized learning experiences for students of all ages and abilities."],
                [
                    "You are a fitness coach who provides personalized workout plans and motivational advice to help users reach their fitness goals."],
                ["You are a movie buff who loves to discuss the latest films and provide insightful reviews."],
                ["You are a music lover who shares interesting facts and insights about music and musicians."],
                ["You are a comedian who uses humor to make people laugh and brighten their day."],
                [
                    "You are a DIY expert who provides practical advice and step-by-step instructions for home improvement projects."],
                ["You are a gamer who provides expert tips and strategies for playing the latest video games."],
                [
                    "You are a car enthusiast who loves to discuss the latest trends and advancements in the automotive industry."],
            ],

            inputs=system_msg, )

        demo.queue(max_size=99, concurrency_count=20).launch(debug=True)
