import zipfile
from io import BytesIO
from random import shuffle

import numpy as np
import pandas as pd
import streamlit as st


def preprocess_file(links: list,
                    contents: str):
    # shuffle link arr
    shuffle(links)

    # replace links template
    for num, link in enumerate(links):
        contents = contents.replace(f'http://{num+1}.com', link)

    return contents


def process_link_array(link_groups, links_number):
    links_2d_array = []
    counts_list = link_groups['link_counts']
    links_list = link_groups['links']
    for num, links in zip(counts_list, links_list):
        links_array = []
        for i in range(len(links)):
            li = list(links[i: i+links_number])
            if len(li) != links_number:
                li.extend(links[:(links_number-len(li))])
            links_array.append(li)
        links_2d_array.extend(links_array * int(num/links_number))
    return links_2d_array

def streamlit_app():
    st.header("Links replacer")

    st.subheader("Text templates:")
    uploaded_files = st.file_uploader("choose texts (allow multiple files):",
                                      accept_multiple_files=True)
    files_dict = {}
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_data = uploaded_file.read().decode("utf-8")
            files_dict[uploaded_file.name] = file_data
        st.write(f"{len(files_dict)} files uploaded.")

    st.subheader("CSV with links:")
    uploaded_csv = st.file_uploader(label="choose csv (allow single file):")

    if uploaded_csv is not None:
        df = pd.read_csv(uploaded_csv)
        st.write(df)

    if files_dict and uploaded_csv is not None:
        st.subheader("Parameters:")
        columns_array = np.array(df.columns)
        col1, col2 = st.columns(2)
        with col1:
            url_option = st.selectbox('URL column',
                                    columns_array,
                                    index=0)
        with col2:
            count_option = st.selectbox('Count column',
                                        columns_array,
                                        index=(len(columns_array)-1))

        count_list = list(set(df[count_option].values))
        if len(count_list) > 5:
            st.write("too many groups founded (>5), change 'Count column'")
        else:
            col1, *cols = st.columns(2)
            with col1:
                links_number = st.number_input(
                    'choose number of link tepmplates in text file:',
                    min_value=1,
                    max_value=20,
                    value=5)

            st.write("Suggested groups:")
            link_groups = {
                "link_counts": [],
                "links": []
            }
            for n_col, col in enumerate(st.columns(len(count_list))):
                with col:
                    st.caption(f"Group {n_col+1}")
                    try:
                        i0, i1 = count_list[n_col].split("-")
                        value = links_number
                        for i in range(int(i0), int(i1)+1):
                            if i % links_number == 0:
                                value = i
                    except Exception:
                        value = links_number
                    number = st.number_input('Choose count:',
                                            key=n_col,
                                            min_value=links_number,
                                            value=value,
                                            step=links_number)
                    group_df = df[df[count_option] == count_list[n_col]]
                    group_df = group_df.copy()
                    st.write(group_df.reset_index(drop=True))
                    link_groups['link_counts'].append(number)
                    link_groups['links'].append(group_df[url_option].values)

            st.markdown("""
                        <style>
                        div.stButton > button:first-child {
                            background-color: rgb(236, 90, 83);
                            width: 22em;
                        }
                        div.stButton > button:first-child:hover {
                            text-decoration:underline;
                            color: rgb(0, 0, 0);
                        }
                        div.stButton > button:first-child:active {
                            text-decoration:underline;
                            color: rgb(0, 0, 0);
                        }
                        div.stButton > button:first-child:visited {
                            text-decoration:underline;
                            color: rgb(0, 0, 0);
                        </style>""", unsafe_allow_html=True)

            _, col2, *_ = st.columns(4)
            with col2:
                st.text("")
                process = st.button('Process')
            if process:
                links_2d_array = process_link_array(link_groups, links_number)

                if len(files_dict) < len(links_2d_array):
                    st.write(f"Need more files, at least {len(links_2d_array)}."
                            f"You upload {len(files_dict)}")
                else:
                    mem_file = BytesIO()
                    zip_file = zipfile.ZipFile(mem_file, 'w', 
                                               zipfile.ZIP_DEFLATED)
                    for links, filename in zip(links_2d_array,
                                            list(files_dict.keys(
                                            ))[:len(links_2d_array)]):
                        zip_file.writestr(filename,
                                        str.encode(preprocess_file(
                                            links,
                                            files_dict[filename])))

                    zip_file.close()
                    
                    _, col2, *_ = st.columns(4)
                    with col2:
                        st.write(
                            f"🎉 {len(links_2d_array)} files processed!")
                        st.markdown("""
                            <style>
                            div.stDownloadButton > button:first-child {
                                width: 22em;
                            }
                            </style>""", unsafe_allow_html=True)
                        st.download_button('Download archive',
                                        mem_file.getvalue(),
                                        "archive.zip",
                                        mime='application/zip',
                                        )


if __name__ == '__main__':
    streamlit_app()
