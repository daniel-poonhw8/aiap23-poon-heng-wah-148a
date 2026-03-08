#!/bin/bash

# ML Pipeline Runner Script

echo "Online Shopping ML Pipeline"

# Check arguments
if [ "$1" = "train" ]; then
    echo "Running training pipeline..."
    PYTHONPATH=src python src/pipeline.py --config config.yaml
elif [ "$1" = "app" ]; then
    echo "Starting Streamlit app..."
    streamlit run app.py
elif [ "$1" = "presentation" ]; then
    echo "Creating presentation..."
    python create_presentation.py
else
    echo "Usage: $0 {train|app|presentation}"
    echo "  train        - Run the ML training pipeline"
    echo "  app          - Start the Streamlit web application"
    echo "  presentation - Generate PowerPoint presentation"
    exit 1
fi

echo "Operation completed."