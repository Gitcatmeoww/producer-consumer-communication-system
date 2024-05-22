FROM python:3.12.3

# Set the working directory in the container
WORKDIR /producer-consumer

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Default command to run
CMD ["python"]
