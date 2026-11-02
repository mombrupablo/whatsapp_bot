This project is about creating a whatsapp bot to interact with a user and collect information for a CRM leads module.

------------------
1. Current status:
------------------
The bot has been implemented with a basic functionality (POC). The bot responds to a few hardcoded input words.

------------------------------------
2. The stack used to create the bot:
------------------------------------
2.1. Python: 
The code to integrate with the whatsapp API and to respond based on the input from the whatsapp user's session is in Python. The program is called app.py.

2.2. Web Application: 
A web application has been created using Flask. The logs information is shown in a web page through the web application.

2.3. Meta Whatsapp API: 
This is the API provided by Meta to interact with Whatsapp. To access this API, the following parameters are informed:
- An authentication token provided by Meta. It exists in an environment variable.
- A phone number and ID provided by Meta. This is the phone number used as the bot.
- A destination phone number. This is my personal cell phone that acts as the requesting user.
The three parameters are saved in environment variables, so they're not in the repository.

2.4. Render Cloud Server: 
As the Meta whatsapp API requires a cloud server for the integration, I'm using Render.
The Render server is plugged into the repository, so every commit executes a new built and deployement of the changes/new objects into the server.
The server is already configured to allow the integration between the python's app and Meta.
I'm currently the only user that can access and configure the Render server as well as access to the Meta app used for the integration.

2.5 SQLite DB: 
A small DB with only one table called Log is used to register the responses from the user, no keys are saved.
The table includes the following columns:
- Date (Datetime)
- Log ID (Auto Generated)
- Text (Text)
This DB runs in the Render server and it can also run in a local environment. The DB is managed by the python's app.

----------
3. Stage 1
----------
The current functionality serves as a POC. The objective of this stage is to extend the current functionality to a CRM context.
The new tasks to consider are:
- Define and Create a complete flow with a number of questions and different branches to collect the user's information through the bot functionality.
- Persist the user's data as a lead to be contacted in the future. This includes the following CRM entities:
-- Lead.
-- Opportunity.
-- Contact.
- Improve the logging functionality by registering the completed interaction between the user and the bot. This includes API errors, Render errors, Python errors.
- Add the functionality to prevent registering twice a lead or a response of the user.
- Analyze, design and create the DB schema that will be used based on the requirements.
- Generate documentation for:
-- The project.
-- The python's code.
-- The web application.
-- The database's schema, including:
--- Tables.
--- Primary keys.
--- Foreign Keys.
--- Indexes.
--- Joins.
--- Any other resources added to the database.
- Ensure that the best practices for coding and database management are used.

As the stack for this stage, I'll use:
- Python for the main app (app.py).
- Flask library.
- Meta's API.
- Render Cloud Server.
- PostgreSQL DB (instead of SQLite) as the DB.

------------------------------------
4. Use Cases to consider in Stage 1:
------------------------------------
4.1 Start a conversation by the user through whastapp.
A person writes a word or text and the system identifies de user's information if exists, and starts a conversation.
4.2. The bot answers the question.
The bot uses a flow to show an initial menu and saves the answer of the user, and continues with the next question in the flow.
4.3. The user responds in a defined period of time.
There will be a specific period of time for the user to respond. After that period, the bot will show the initial menu again after user's input.
4.4. Creation of the lead in the database after the last response of the user.
The creation of the lead, will also involve the creation of a contact and an opportunity associated to the lead.
4.5. Avoid duplication of leads.
4.6. Failures in the response of the application.
Specific number of reintent must be done by the application to ensure that the lead is created. If the creation fails after those intents, the lead must be temporarily register and persisted once the issues are solved.
4.7. Log all the interaction between the bot and the user.

---------------
5. Second Stage
---------------
Once the fist stage is deployed, the following requirements must be included as part of a next stage:
5.1. Administrative Panel to access all the registered information of the user.
5.2. Dashboard and metrics based on the CRM entities information.
5.3. Editor of questions and flows.
5.4. Catalog of products with prices and stocks.
