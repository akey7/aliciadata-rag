import os
import logging
import time
import datetime
from openai import OpenAI
from openai import APIError, APIConnectionError
import anthropic
import chevron


class AgentMixin:
    """
    AgentMixin provides common functionality to all agents that use
    OpenAI, Anthropic API calls.
    """

    def crash_report_filename(self):
        """
        Generate a date/time-stamped crash report filename.

        Returns
        -------
        str
            Absolute path to a crash report filename.
        """
        knowledge_agent_data_dir = os.getenv("KNOWLEDGE_AGENT_DATA_FOLDER")
        crash_reports_dir = os.path.join(knowledge_agent_data_dir, "crash_reports")
        if not os.path.exists(crash_reports_dir):
            raise FileNotFoundError(
                f"AgentMixin: crash_reports_folder {crash_reports_dir} does not exist."
            )
        stamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        filename = os.path.join(crash_reports_dir, f"crash_report_{stamp}.md")
        return filename

    def prepare_prompt_from_file(self, prompt_name, data=None):
        """
        Load a prompt from the prompts folder and optionally interpolate
        values into it.

        Parameters
        ----------
        prompt_name : str
            The name of the prompt (without extension) in the prompts folder

        data : dict
            Defaults to None. If None, no interpolation is applied. If a
            dictionary, Chevron is used to interpolate values into the
            result according to the mustache templating language.

        Returns
        -------
        str
            The contents of the prompt, interpolated with data if given.
        """
        prompt_path = os.path.join("prompts", f"{prompt_name}.mustache")
        if data:
            with open(prompt_path, "r", encoding="utf-8") as f:
                contents = chevron.render(f, data)
        else:
            with open(prompt_path, "r", encoding="utf-8") as f:
                contents = f.read()
        return contents

    def call_openai_with_messages(
        self,
        messages,
        notifier=None,
        model="gpt-5-mini",
        pause_between_prompts=60,
        max_retries=5,
        base_delay=2,
    ):
        """
        Call the OpenAI API.

        Parameters
        ----------
        system_content : str
            System prompt content.

        user_content : str
            User prompt content.

        notifier : NotificationWorkflow, optional
            The NotificatioWorkflow that can send notifications about errors.
            No success notifications are sent by this method.

        pause_between_prompts : int, optional
            Delay between prompts. This is the sleep duration between successful
            completion and return.

        max_retries : int, optional
            Maximum number of retries if there are network errors. Defaults
            to 5.

        base_delay : int, optional
            The base delay for exponential back off in seconds. Defaults
            to 1.

        Returns
        -------
        Tuple[str, str]
            The model and the response strings, in that order.
        """
        retries = 0
        while retries < max_retries:
            try:
                logging.info(f"AgentMixin: call_openai() {model}")
                client = OpenAI()
                completion = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    reasoning_effort="minimal",
                )
                logging.info(f"AgentMixin: Sleeping {pause_between_prompts} seconds...")
                time.sleep(pause_between_prompts)
                return model, completion.choices[0].message.content
            except (APIError, APIConnectionError) as e:
                retries += 1
                delay = base_delay * (2**retries)
                logging.error(
                    f"AgentMixin: Retrying OpenAI in {delay} seconds due to error: {e}. Attempt {retries} of {max_retries}"
                )
                time.sleep(delay)
            except Exception as e:
                error_message = f"AgentMixin: OpenAI call error: {e}"
                logging.error(error_message)
                if notifier:
                    notifier.send_notification(error_message)
                break
        error_message = (
            f"AgentMixin: Failed to complete the request after {max_retries} attempts."
        )
        logging.error(error_message)
        if notifier:
            notifier.send_notification(error_message)
        return model, None

    def call_anthropic(
        self,
        system_content,
        user_content,
        notifier=None,
        pause_between_prompts=60,
        model="claude-haiku-4-5",
    ):
        """
        Call the Anthropic API.

        Parameters
        ----------
        system_content : str
            System prompt content.

        user_content : str
            User prompt content.

        notifier : NotificationWorkflow, optional
            The NotificatioWorkflow that can send notifications about errors.
            No success notifications are sent by this method. If this
            parameter is None, no error notifications are sent.

        pause_between_prompts : int, optional
            Delay between prompts in seconds. This is the sleep duration between
            successful completion and return.

        Returns
        -------
        Tuple[str, str]
            The model and the response strings, in that order.
        """
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        client = anthropic.Anthropic(
            api_key=anthropic_api_key,
        )
        try:
            logging.info(f"AgentMixin: call_anthropic(): {model}")
            message = client.messages.create(
                model=model,
                max_tokens=8192,
                temperature=0,
                system=system_content,
                messages=[
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": user_content}],
                    }
                ],
            )
            logging.info(f"AgentMixin: Sleeping {pause_between_prompts} seconds...")
            time.sleep(pause_between_prompts)
            return model, (
                message.content[0].text
                if isinstance(message.content, list)
                else message.content
            )
        except anthropic.APIConnectionError as e:
            error_message = f"AgentMixin: Anthropic connection error {e}"
            logging.error(error_message)
            if notifier:
                notifier.send_notification(error_message)
            logging.info(f"AgentMixin: Sleeping {pause_between_prompts} seconds...")
            time.sleep(pause_between_prompts)
            return None
