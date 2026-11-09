# Monkey Messenger

This is a hobby project to connect to an esp32 and display messages/pictures on an LCD display. I plan on gifting the hardware to my long distance girlfriend for her to display the messages I send on her desk!

The idea is to have the esp32 repeatedly make calls to this web API, which will send the latest message that has been stored in the database.

```mermaid
graph LR
    %% Custom Styling
    classDef frontend fill:#22272d,stroke:#8d9855,stroke-width:2px,color:#8d9855,font-weight:bold;
    classDef api fill:#22272d,stroke:#4b8eab,stroke-width:2px,color:#4b8eab,font-weight:bold;

    %% Nodes and Connections
    A["Web Frontend"] <--> B["API Gateway"]
    B <--> C["ESP32 Display"]

    %% Custom Styling for Arrows
    %% 0 is the first arrow (A <--> B), 1 is the second arrow (B <--> C)
    linkStyle 0 stroke:#c49852,stroke-width:3px;
    linkStyle 1 stroke:#c49852,stroke-width:3px;

    %% Assigning Styles
    class A frontend;
    class B api;
    class C frontend;
```

The code and setup for the esp32 can be found in my [other repo](https://github.com/Cristian-Cortez/Monkey-Messenger-ESP32). This repo contains my simple Django web app code that I have hosted [here](https://cristianwuzhear.pythonanywhere.com/). I found that pythonanywhere is a perfect way to host a hobby project like this due to it's free tier, the only downside is that I cant give it a custom domain name without paying a monthly subscription.

## Requirements

1. A python virtual environment containing all packages in `requirements.txt`
2. A .env file containing the structure of the `.env-example`

After cloning repo and activating your virtual environment, run:

```bash
    python manage.py makemigrations monkey_messages
    python manage.py migrate
    python manage.py runserver 0.0.0.0:8000
```

Use `0.0.0.0:8000` to test esp32 connection locally, so you can access the localhost through your ip address.


## API

The API is currently setup as follows:

| Route                         | Type | Description                                 |
|-------------------------------|------|---------------------------------------------|
| `api/monkey_messages`         | POST | adds a new message to the database          |
| `api/monkey_messages/latest`  | GET  | gets the most recent message that was added |
| `api/monkey_messages/history` | GET  | gets the most recent 50 messages            |

As a basic security measure, I am using an X-API-KEY header for all routes. This is stored in a .env as SECRET_KEY. The frontend of this application is setup so that the messages cannot be viewed unless this key is entered in the input field. Additionally, this means the esp32 will need to use this key to use the GET routes.

## Database

This is a single-page application that uses a sqlite database. This was the simpliest for this project due to only needing 1 table (model) to be stored and not having to use an external database. (also using pythonanywhere's inhouse sql db requires a paid subscription)

While Django models are a bit of a learning curve if you are used to using raw SQL, it can make up for it in speed and maintenance. It can be very convinent to only need to update the `models.py` and keep everything in python, rather than switching over to an external db GUI and make the changes there.

My current Monkey_Message model is as follows:

| Field          | Type          | Description                           |
|----------------|---------------|---------------------------------------|
| `text`         | TextField     | message text                          |
| `image`        | ImageField    | message image for web frontend access |
| `image_base64` | TextField     | message image for esp32 access        |
| `created_at`   | DateTimeField | est time of when the message was sent |

One architectural decision that I found interesting was to use separate fields for the web frontend image and the esp32 image. My initial thought was to store the images in base64 and have that take care of both frontends. However, it made more sense to use Django's `ImageField` which stores full copies of the images in a local directory, which can be accessed through a url given by the model:

```python
"image_url": request.build_absolute_uri(message.image.url)
```

A pro of this decision was that the browser caches image files automatically, which cuts load times from converting the base64 images from the api response with each refresh. An initial con that you might think of is that locally storing full images can lead to expensive storage, especially with high resolution images. However, with an image compression function, images can be shrunk from ~2.6mb each to ~6kb, which considering pythonanywhere's free 512mb storage, allows for more than enough photos for me to store for this project.

## Backlog

Some small things I plan on adding as I work on this more:

1. DELETE route for messages that can be access on the web frontend
2. More consistent image orientations. Currently, uploading an image from a phone results in a gamble of whether it will be in the correct orientation or not.

A larger dream is to have multiple esp32 frontends, one for me and one for my gf, and the website will allow for us to send messages from one person to another based off of which API key is used. However, right now I have to polish this current one way connection.
