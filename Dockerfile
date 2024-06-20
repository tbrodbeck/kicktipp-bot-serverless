FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set timezone to European
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt install -y tzdata
RUN apt-get clean
RUN ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime

WORKDIR /app

# Install the Python requirements
## upgrade pip
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY lambda_function.py main.py

# Set display port as an environment variable
ENV DISPLAY=:99RUN

# Run the application
CMD ["python", "main.py", "--headless"]
