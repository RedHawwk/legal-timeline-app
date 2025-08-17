import streamlit as st
import asyncio
from pathlib import Path
import tempfile
import pandas as pd
from src.main import LegalTimelineExtractor

# --- Page Configuration ---
st.set_page_config(
    page_title="Legal Timeline Extractor",
    page_icon="⚖️",
    layout="wide"
)

# --- Main Application UI ---
st.title("⚖️ Legal Document Timeline Extractor")
st.markdown("Upload your legal documents (`.txt`, `.pdf`, `.docx`) below and click 'Process' to generate a chronological timeline.")

# --- File Uploader ---
uploaded_files = st.file_uploader(
    "Choose documents...",
    type=['txt', 'pdf', 'docx'],
    accept_multiple_files=True,
    help="You can upload multiple files at once."
)

# --- Process Button and Logic ---
if st.button("🚀 Process Documents"):
    if uploaded_files:
        # Create a temporary directory to store uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save all uploaded files to the temporary directory
            for uploaded_file in uploaded_files:
                with open(temp_path / uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            
            # Show a spinner while processing
            with st.spinner(f"Processing {len(uploaded_files)} documents... This may take a moment."):
                try:
                    # Initialize and run the extractor
                    extractor = LegalTimelineExtractor(config_path="config.yaml")
                    
                    # Run the async function
                    results_dict = asyncio.run(extractor.process_directory(
                        input_dir=str(temp_path),
                        output_dir=str(temp_path), # Output to temp dir as well
                        output_format='json', # We only need the data
                        max_workers=4
                    ))
                    
                    st.success("✅ Extraction Complete!")
                    
                    # --- Display Summary ---
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Files Processed", results_dict['files_processed'])
                    col2.metric("Events Found", results_dict['events_extracted'])
                    col3.metric("Time Taken", f"{results_dict['processing_time']:.2f}s")
                    
                    # --- Display Results Table ---
                    st.subheader("Extracted Timeline Events")
                    
                    # Load events from the generated JSON for display
                    events_path = temp_path / 'timeline.json'
                    if events_path.exists():
                        df = pd.read_json(events_path)
                        # Reorder columns for better presentation
                        display_columns = ['date', 'event_type', 'description', 'source_file', 'confidence_score']
                        df_display = df[[col for col in display_columns if col in df.columns]]
                        st.dataframe(df_display, use_container_width=True)
                    else:
                        st.warning("Could not find the results file to display.")

                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")

    else:
        st.warning("⚠️ Please upload at least one document.")