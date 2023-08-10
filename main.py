from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.schema import (
    HumanMessage,
    SystemMessage,
)
from config import OPENAI_API_KEY
from camel_agent import CAMELAgent
from colorama import init, Fore, Style
from prompts import editor_prompt, writer_prompt

init()


if __name__ == "__main__":
    editor_role = "Expert Editor"
    writer_role = "Expert Writer"

    task = input("Enter the task you want the writer and editor to collaborate on: ")
    word_limit = 100

    task_specifier_sys_msg = SystemMessage(content="You can make a task more specific.")
    task_specifier_prompt = """Here is a task that {assistant_role_name} will help {user_role_name} to complete: {task}.
    Please make it more specific. Be creative and imaginative.
    Please reply with the specified task in {word_limit} words or less. Do not add anything else."""
    task_specifier_template = HumanMessagePromptTemplate.from_template(
        template=task_specifier_prompt
    )
    task_specifier_msg = task_specifier_template.format_messages(
        assistant_role_name=writer_role,
        user_role_name=editor_role,
        task=task,
        word_limit=word_limit,
    )[0]

    task_specify_agent = CAMELAgent(
        ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0.2),
        task_specifier_sys_msg,
    )
    specified_task_msg = task_specify_agent.step(task_specifier_msg)
    specified_task = specified_task_msg.content

    print(f"{Fore.YELLOW}Original task prompt:\n{task}{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}Specified task prompt:\n{specified_task}{Style.RESET_ALL}\n")

    editor_prompt_template = SystemMessagePromptTemplate.from_template(template=editor_prompt)
    editor_sys_message = editor_prompt_template.format_messages(specified_task=specified_task)[0]
    
    writer_prompt_template = SystemMessagePromptTemplate.from_template(template=writer_prompt)
    writer_sys_message = writer_prompt_template.format_messages(specified_task=specified_task)[0]
    
    writer = CAMELAgent(
        ChatOpenAI(temperature=0.2, openai_api_key=OPENAI_API_KEY),
        writer_sys_message
    )
    editor = CAMELAgent(
        ChatOpenAI(temperature=0.2, openai_api_key=OPENAI_API_KEY),
       editor_sys_message
    )
    writer.reset()
    editor.reset()

    editor_msg = HumanMessage(
        content=(
            f"{editor_sys_message.content}. Now write on the task provided and present a starting draft"
        )
    )

    print(f"{Fore.GREEN}AI {editor_role}:\n\n{editor_msg.content}{Style.RESET_ALL}\n\n")
    writer_response = writer.step(HumanMessage(content=f"{editor_msg.content}"))
    print(
        f"{Fore.GREEN}AI {writer_role}:\n\n{writer_response.content}{Style.RESET_ALL}\n\n"
    )

    chat_turn_limit, n = 30, 0
    while n < chat_turn_limit:
        n += 1

        editor_ai_msg = editor.step(writer_response)
        editor_response = HumanMessage(
            content=editor_ai_msg.content
            + "\nPlease improve the draft based on the guidelines"
        )
        print(
            f"{Fore.GREEN}AI {editor_role}:\n\n{editor_response.content}{Style.RESET_ALL}\n\n"
        )

        if "<CAMEL_TASK_DONE>" in editor_ai_msg.content:
            break

        writer_ai_msg = writer.step(editor_response)
        writer_response = HumanMessage(
            content=writer_ai_msg.content
            + "\n\nAre there any more improvements that can be made? if not please say <CAMEL_TASK_DONE>"
        )
        print(
            f"{Fore.GREEN}AI {writer_role}:\n\n{writer_response.content}{Style.RESET_ALL}\n\n"
        )
