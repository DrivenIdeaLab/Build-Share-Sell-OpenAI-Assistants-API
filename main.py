import openai
import streamlit as st
import time
import os
import zipfile
import yaml

from inference_assistant import inference
from utils import create_assistant_from_config_file, upload_to_openai

st.title("Assistant BUILDER🚧 & SHARING🤗")

utilizzo = st.selectbox("🤖 Hi, what do you want to do?", ("Create or Import an Assistant", "Use an Assistant"))

openaiKey = st.text_input("🔑 Pls insert your OpenAI API Key")


if openaiKey:
    os.environ["OPENAI_API_KEY"] = openaiKey
    openai.api_key = openaiKey
    client = openai.OpenAI()

    if utilizzo != "Use an Assistant":
        scelta_creazione = st.selectbox(
            '💻 Do you want to create an assistant from scratch or import an assistant?',
            ('Create an Assistant from Scratch', 'Import an Assistant from .iaItaliaBotConfig'),
            index=0
        )

        if scelta_creazione == "Create an Assistant from Scratch":
            col1, col2 = st.columns(2)

            with col1:
                nome_assistente = st.text_input("👶 Insert the name of the assistant")

            with col2:
                modello_assistente = st.selectbox(
                    '🛒 Choose the model of the assistant',
                    ('gpt-4-1106-preview', 'gpt-4'),
                    index=0
                )

            if nome_assistente and modello_assistente:
                prompt_sistema = st.text_area("📄 Write the instructions for the assistant")

                carica_file = st.checkbox("📚 Do you want to upload files for knowledge?")

                stored_file = []
                if carica_file:
                    file_up = st.file_uploader("📚 Upload File", type=['csv', 'txt', 'pdf', 'ipynb'], accept_multiple_files=True)
                    if file_up:
                        if len(file_up) > 20:
                            st.error("🛑 You can upload a maximum of 20 files")
                            st.stop()
                        st.info("HEY, Remember to click on the button 'Upload File' to upload the files to OpenAI")
                        if st.button("📩 Upload File"):
                            with st.status("📡 Upload File on OpenAI Server...", expanded=True) as status:
                                for file in file_up:
                                    time.sleep(2)
                                    status.update(label="🛰 Upload File: " + file.name)
                                    with open(file.name, "wb") as f:
                                        f.write(file.getbuffer())
                                    additional_file_id = upload_to_openai(file)
                                    if additional_file_id:
                                        st.write("File uploaded successfully: " + file.name + " with ID: " + additional_file_id)
                                        stored_file.append(additional_file_id)
                                st.write("👌 Files uploaded successfully: " + str(len(stored_file)))
                                if 'id_file' not in st.session_state:
                                    st.session_state.id_file = []
                                st.session_state.id_file = stored_file
                                status.update(label="Files uploaded successfully", state="complete", expanded=False)

                if st.button("🤖 Build Assistant") and prompt_sistema:
                    with st.status("⏲ Assistant creation in progress...", expanded=True) as status:
                        time.sleep(2)
                        status.update(label="🧐 Configuring the assistant...", state="running")
                        time.sleep(2)
                        if "id_file" in st.session_state and len(st.session_state.id_file) > 0:
                            status.update(label="📡 Create Assistant with File and Retrieval...", state="running")
                            my_assistant = client.beta.assistants.create(
                                instructions=prompt_sistema,
                                name=nome_assistente,
                                tools=[{"type": "retrieval"}],
                                model=modello_assistente,
                                file_ids=st.session_state.id_file,
                            )
                            st.write("👌 Assistant created successfully with File and Retrieval")
                        else:
                            
                            my_assistant = client.beta.assistants.create(
                                instructions=prompt_sistema,
                                name=nome_assistente,
                                model=modello_assistente,
                            )
                            status.update(label="👌 Assistente creato con successo", state="complete")


                        time.sleep(1)

                        st.success("Assistente creato con successo")
                        st.info("L'ID dell'assistente è: " + my_assistant.id)
                        st.error("Ricorda di salvare l'ID dell'assistente per utilizzarlo in seguito")
                        st.success("Per utilizzare l'assistente importato, copia l'ID e incollalo nella sezione 'Usa un Assistente'")


                    col3, col4 = st.columns(2)
                    #crea un bottone per scaricare un file.txt con l'ID dell'assistente
                    col3.download_button(
                        label="🗂 Download ID Assistant",
                        data="ASSISTANT ID : " + my_assistant.id + "\nOpenAI API Key: " + openaiKey,
                        file_name="id_ASSISTANT_" + nome_assistente.replace(" ", "_") + ".txt",
                        mime="text/plain",
                    )

                    with st.spinner("📥 Building Assistant Configuration File..."):
                        time.sleep(2)
                        
                        #CREO IL FILE DI CONFIGURAZIONE YAML con i dati dell'assistente : Nome, Modello, Sistem_prompt
                        file_yaml = open("config_assistente.yaml", "w")
                        file_yaml.write("name: " + nome_assistente + "\n")
                        file_yaml.write("model: " + modello_assistente + "\n")
                        file_yaml.close()

                        #Crea file.txt per sistem_prompt
                        file_prompt = open("prompt.txt", "w")
                        file_prompt.write(prompt_sistema)
                        file_prompt.close()


                        #CREO IL FILE ZIP
                        zip_file = zipfile.ZipFile("config_assistente.zip", "w")
                        zip_file.write("config_assistente.yaml")
                        zip_file.write("prompt.txt")

                        if file_up:
                            for file in file_up:
                                with open(file.name, "rb") as f:
                                    zip_file.write(file.name)
                        zip_file.close()

                        #cambia estensione e nome del file nome_assistente.iaItaliaBotConfig e st.download_button
                        col4.download_button(
                            label="🗂 Download Assistant Configuration File",
                            data=open("config_assistente.zip", "rb"),
                            file_name=nome_assistente + ".iaItaliaBotConfig",
                            mime="application/zip",
                        )


                        st.balloons()


        else:
            file_up = st.file_uploader("Carica il file .iaItaliaBotConfig", type=['iaItaliaBotConfig'], accept_multiple_files=False)
            if file_up:
                if st.button("Crea Assistant Importato"):
                    client = openai.OpenAI()
                    my_assistant = create_assistant_from_config_file(file_up, client)

                    with st.status("Creazione assistente importato in corso...", expanded=True) as status:
                        time.sleep(2)
                        status.update(label="Assistente importato creato con successo", state="complete")

                        st.success("Assistente importato creato con successo")
                        st.info("L'ID dell'assistente importato è: " + my_assistant.id)
                        st.error("Ricorda di salvare l'ID dell'assistente per utilizzarlo in seguito")
                        st.success("Per utilizzare l'assistente importato, copia l'ID e incollalo nella sezione 'Usa un Assistente'")

                    st.download_button(
                        label="Scarica l'ID dell'assistente importato",
                        data="ID dell'assistente: " + my_assistant.id + "\nOpenAI API Key: " + openaiKey,
                        file_name="id_assistente.txt",
                        mime="text/plain",
                    )


    else:
        # Inferenza con Assistente

        id_assistente = st.text_input("Inserisci l'ID dell'assistente")

        if id_assistente:
            inference(id_assistente)