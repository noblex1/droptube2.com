import streamlit as st
from pytube import YouTube
from pytube.exceptions import PytubeError
from PIL import Image
from io import BytesIO
import requests
import os
import traceback

# Streamlit configuration
st.set_page_config(
    page_title="DropTube - YouTube Downloader",
    page_icon=":arrow_down:",
    layout="wide"
)

# Streamlit custom styles
st.markdown("""
<style>
    .stApp { background-color: #f5f5f5; font-family: 'Segoe UI', sans-serif; }
    .title { font-size: 42px; font-weight: bold; color: #0d47a1; text-align: center; margin-bottom: 0; }
    .subtitle { font-size: 20px; color: #555; text-align: center; margin-top: 0; margin-bottom: 20px; }
    .block-container { padding-top: 2rem; }
    .footer { font-size: 12px; color: #888; text-align: center; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# Streamlit title and subtitle
st.markdown('<p class="title">DropTube - YouTube Downloader</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Download your favorite videos or audio with ease.</p>', unsafe_allow_html=True)

# Initialize session state for download history
if "history" not in st.session_state:
    st.session_state["history"] = []

# Input field for YouTube URL
url = st.text_input(
    "Enter YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Paste the URL of the YouTube video you want to download."
)

if url:
    try:
        # Initialize YouTube object
        yt = YouTube(url)

        # Display video preview and details
        col1, col2 = st.columns([1, 2])
        with col1:
            if yt.thumbnail_url:
                response = requests.get(yt.thumbnail_url)
                img = Image.open(BytesIO(response.content))
                st.image(img, use_column_width=True, caption="Video Thumbnail")
            else:
                st.warning("Thumbnail not available for this video.")
        with col2:
            st.subheader(yt.title)
            st.write(f"**Length:** {yt.length // 60} min {yt.length % 60} sec")
            st.write(f"**Views:** {yt.views:,}")
            st.write(f"**Published on:** {yt.publish_date.strftime('%b %d, %Y') if yt.publish_date else 'Unknown'}")
            st.write(f"**Channel:** {yt.author}")

        st.markdown("---")

        # Select download type
        download_type = st.radio(
            "Download Type",
            ["Video", "Audio"],
            horizontal=True,
            help="Choose whether to download the video or audio."
        )

        # Video download logic
        if download_type == "Video":
            streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
            if streams:
                options = [f"{stream.resolution} ({round(stream.filesize / 1024 / 1024, 2)} MB)" for stream in streams]
                selected = st.selectbox("Select Resolution", options, help="Select your preferred video resolution.")
                selected_res = selected.split()[0]
                format_option = st.selectbox("Convert To Format (Optional)", ["mp4", "webm", "mov", "avi"])
                if st.button("Download Video"):
                    with st.spinner("Processing your video download..."):
                        try:
                            stream = streams.filter(res=selected_res).first()
                            out_file = stream.download()
                            new_filename = out_file.replace(".mp4", f".{format_option}")
                            os.rename(out_file, new_filename)
                            with open(new_filename, "rb") as file:
                                st.download_button(
                                    label="Click to Download",
                                    data=file,
                                    file_name=os.path.basename(new_filename),
                                    mime="video/mp4"
                                )
                            st.success("Video downloaded successfully!")
                            st.session_state["history"].append({"type": "Video", "title": yt.title, "format": format_option})
                        except Exception as e:
                            st.error(f"An error occurred during download: {e}")
                            st.text(traceback.format_exc())
                        finally:
                            if os.path.exists(new_filename):
                                os.remove(new_filename)
            else:
                st.error("No video streams available for download.")

        # Audio download logic
        else:
            streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
            if streams:
                options = [f"{stream.abr} ({round(stream.filesize / 1024 / 1024, 2)} MB)" for stream in streams]
                selected = st.selectbox("Select Audio Quality", options, help="Select your preferred audio quality.")
                selected_abr = selected.split()[0]
                format_option = st.selectbox("Convert To Format (Optional)", ["mp3", "aac", "wav", "ogg"])
                if st.button("Download Audio"):
                    with st.spinner("Processing your audio download..."):
                        try:
                            stream = streams.filter(abr=selected_abr).first()
                            out_file = stream.download(filename_prefix="AUDIO_")
                            new_filename = out_file.replace(".mp4", f".{format_option}")
                            os.rename(out_file, new_filename)
                            with open(new_filename, "rb") as file:
                                st.download_button(
                                    label="Click to Download",
                                    data=file,
                                    file_name=os.path.basename(new_filename),
                                    mime="audio/mpeg"
                                )
                            st.success("Audio downloaded successfully!")
                            st.session_state["history"].append({"type": "Audio", "title": yt.title, "format": format_option})
                        except Exception as e:
                            st.error(f"An error occurred during download: {e}")
                            st.text(traceback.format_exc())
                        finally:
                            if os.path.exists(new_filename):
                                os.remove(new_filename)
            else:
                st.error("No audio streams available for download.")

        st.markdown("---")

        # Display download history
        if st.session_state["history"]:
            st.subheader("Download History")
            for item in st.session_state["history"][::-1]:
                st.markdown(f"- **{item['type']}**: {item['title']} ({item['format']})")

            # Option to clear history
            if st.button("Clear History"):
                st.session_state["history"] = []
                st.success("Download history cleared!")

    except PytubeError as e:
        st.error(f"Failed to fetch YouTube video: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.text(traceback.format_exc())

# Footer
st.markdown('<p class="footer">DropTube © 2025 - Built with ❤️ using Streamlit</p>', unsafe_allow_html=True)
