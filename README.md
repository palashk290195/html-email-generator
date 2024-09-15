# html-email-generator
# AI-Powered Email HTML Generator

This project is an AI-powered email HTML generator that allows users to create professional, customized email templates using OpenAI's GPT model. It features theme extraction from websites, logo handling, and pre-defined email template selection.

## Features

- Generate HTML email content using OpenAI's GPT model
- Extract logo & color themes from website
- Fetch or upload logos for email templates
- Select from pre-defined email templates or create custom ones
- Preview email templates before generation
- Real-time chat interface for customizing email content
- Copy generated HTML with a single click

## Screenshots

![image](https://github.com/user-attachments/assets/d2232264-2eee-4272-b6a2-5fdad652a1a8)

*Main interface of the Email HTML Generator*

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/palashk290195/html-email-generator.git
   cd html-email-generator
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   Create a `.env` file in the root directory and add the following:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   LOGO_DEV_TOKEN=your_logo_dev_token_here
   UNSPLASH_APPLICATION_ID=your_unsplash_application_id_here
   UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
   UNSPLASH_SECRET_KEY=your_unsplash_secret_key_here
   ```

5. Run the Flask application:
   ```
   flask --app app run
   ```

6. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Enter a website URL to extract its color theme and logo.
2. Select an email template from the dropdown or choose "None" for a custom template.
3. Preview the selected template using the "Preview Template" button.
4. Enter your OpenAI API key, profile details, and specific instructions for the email content.
5. Click "SEND" to generate the email HTML.
6. Use the "Toggle Preview/Code" button to switch between the visual preview and HTML code.
7. Copy the generated HTML using the "COPY HTML" button.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- OpenAI for providing the GPT model
- Flask for the web framework
- Bootstrap for the frontend styling
