import gradio as gr
import xxhash
from gradio.components import _Keywords
from ai import AI
from config import Config
from contents import *
from storage import Storage

def webui(cfg: Config):
    """Run the web UI."""
    Webui(cfg).run()

class Webui:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.ai = AI(cfg)

    def _save_to_storage(self, contents, hash_id):
        print(f"Saving to storage {hash_id}")
        print(f"Contents: \n{contents}")
        self.storage = Storage.create_storage(self.cfg)
        if self.storage.been_indexed(hash_id):
            return 0
        else:
            embeddings, tokens = self.ai.create_embeddings(contents)
            self.storage.add_all(embeddings, hash_id)
            return tokens

    def _get_hash_id(self, contents):
        return xxhash.xxh3_128_hexdigest('\n'.join(contents))

    def run(self):
        with gr.Blocks() as demo:
            hash_id_state = gr.State()
            init_page = gr.Column()
            chat_page = gr.Column(visible=False)

            with init_page:
                with gr.Tab("file"):
                    file_error_box = gr.Textbox(label="Input Error", visible=False)
                    file_box = gr.File(label="File", file_types=["pdf", "txt", "docx"])
                    file_submit_btn = gr.Button("Submit file", variant="primary")
                    def submit(file):
                        url = file.name
                        if url.endswith('.pdf'):
                            contents, lang = extract_text_from_pdf(url)
                        elif url.endswith('.txt'):
                            contents, lang = extract_text_from_txt(url)
                        elif url.endswith('.docx'):
                            contents, lang = extract_text_from_docx(url)
                        else:
                            return {file_error_box: gr.update(value="Can not read this file", visible=True)}
                        if len(contents) == 0:
                            return {file_error_box: gr.update(value="Empty file", visible=True)}
                        hash_id = self._get_hash_id(contents)
                        self._save_to_storage(contents, hash_id)
                        return {
                            init_page: gr.update(visible=False),
                            chat_page: gr.update(visible=True),
                            file_box: gr.update(value=_Keywords.NO_VALUE),
                            file_error_box: gr.update(visible=False),
                            hash_id_state: hash_id
                        }
                    file_submit_btn.click(
                        submit,
                        [file_box],
                        [init_page, chat_page, file_box, file_error_box, hash_id_state],
                    )

            with chat_page:
                with gr.Row():
                    with gr.Column():
                        chatbot = gr.Chatbot(height=800)
                        msg = gr.Textbox(label="Query")
                        submit_box = gr.Button("Submit", variant="primary")
                        reset_box = gr.Button("Reset")
                    with gr.Column():
                        dataset_box = gr.Dataset(components=[gr.Textbox(visible=False)],
                                                 label="Context",
                                                 samples=[],
                                                 visible=False,
                                                 )
                def respond(message, chat_history, hash_id):
                    kw = self.ai.get_keywords(message)
                    if len(kw) == 0 or hash_id is None:
                        return "", chat_history
                    _, kw_ebd = self.ai.create_embedding(kw)
                    ctx = self.storage.get_texts(kw_ebd, hash_id)
                    print(f"Context: \n{ctx}")
                    bot_message = self.ai.completion(message, ctx)
                    chat_history.append((message, bot_message))
                    return "", chat_history, dataset_box.update(samples=[[item] for item in ctx][:20], visible=True)
                def reset():
                    return {
                        init_page: gr.update(visible=True),
                        chat_page: gr.update(visible=False),
                        chatbot: gr.update(value=[]),
                        msg: gr.update(value=""),
                        hash_id_state: None,
                    }
                msg.submit(respond, [msg, chatbot, hash_id_state], [msg, chatbot, dataset_box])
                submit_box.click(respond, [msg, chatbot, hash_id_state], [msg, chatbot, dataset_box])
                reset_box.click(reset, None, [init_page, chat_page, chatbot, msg, dataset_box, hash_id_state])

        demo.title = "Chat With Doc"
        demo.launch(server_port=self.cfg.webui_port, server_name=self.cfg.webui_host, show_api=False, share=True)
