import json
import os
import pathlib
import time
import matplotlib.pyplot as plt
import numpy as np  # For color mapping
from dotenv import load_dotenv

# Import Kafka only if available
try:
    from kafka import KafkaConsumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

# Import logging utility
from utils.utils_logger import logger

#####################################
# Load Environment Variables
#####################################

load_dotenv()

#####################################
# Getter Functions for Environment Variables
#####################################

def get_kafka_topic() -> str:
    return os.getenv("PROJECT_TOPIC", "buzzline-topic")

def get_kafka_server() -> str:
    return os.getenv("KAFKA_SERVER", "localhost:9092")

#####################################
# Set up Paths
#####################################

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
DATA_FOLDER = PROJECT_ROOT.joinpath("data")
DATA_FILE = DATA_FOLDER.joinpath("project_live.json")

#####################################
# Set up live visualization
#####################################

plt.ion()  # Turn on interactive mode
fig, ax = plt.subplots()
message_lengths = []
length_counts = {}  # Dictionary to store message length frequencies

def update_chart():
    """
    Update the live bar chart for message length frequency.
    """
    ax.clear()
    if not message_lengths:
        return

    # Sort the dictionary by message length
    sorted_lengths = sorted(length_counts.keys())
    counts = [length_counts[length] for length in sorted_lengths]

    # Generate unique colors for bars
    colors = plt.cm.viridis(np.linspace(0, 1, len(sorted_lengths)))

    # Create the bar chart
    ax.bar(sorted_lengths, counts, color=colors)
    ax.set_xlabel("Message Length")
    ax.set_ylabel("Count")
    ax.set_title("Counts of Messages by Message Length")
    ax.set_xticks(sorted_lengths)

    plt.draw()
    plt.pause(0.1)  # Allow time for the chart to render

#####################################
# Define Message Consumer
#####################################

def consume_from_kafka():
    """
    Consume messages from a Kafka topic.
    """
    topic = get_kafka_topic()
    kafka_server = get_kafka_server()
    
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=kafka_server,
            value_deserializer=lambda x: json.loads(x.decode("utf-8"))
        )
        logger.info(f"Kafka consumer connected to {kafka_server}, listening to topic '{topic}'")
        
        for message in consumer:
            logger.info(f"Received from Kafka: {message.value}")
            process_message(message.value)
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}")

def consume_from_file():
    """
    Consume messages from the JSON file if Kafka is unavailable.
    """
    if not DATA_FILE.exists():
        logger.error("Data file not found.")
        return
    
    logger.info(f"Reading messages from {DATA_FILE}")
    try:
        with DATA_FILE.open("r") as f:
            for line in f:
                message = json.loads(line.strip())
                logger.info(f"Read from file: {message}")
                process_message(message)
                time.sleep(1)  # Simulate processing delay
    except Exception as e:
        logger.error(f"Error reading from file: {e}")

def process_message(message: dict):
    """
    Process the incoming message and update the chart.
    """
    logger.info(f"Processing message: {message}")
    message_length = message.get("message_length", 0)
    message_lengths.append(message_length)

    # Update dictionary instead of using Counter
    if message_length in length_counts:
        length_counts[message_length] += 1
    else:
        length_counts[message_length] = 1

    update_chart()

def main():
    logger.info("START consumer...")
    if KAFKA_AVAILABLE:
        consume_from_kafka()
    else:
        logger.warning("Kafka not available, falling back to file consumption.")
        consume_from_file()
    
    plt.ioff()
    plt.show()
    
#####################################
# Conditional Execution
#####################################

if __name__ == "__main__":
    main()
