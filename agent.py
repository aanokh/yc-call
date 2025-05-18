import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio
from fastapi import FastAPI, Form, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
import json
import os
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# ── MCP subprocess handles ──────────────────────────────────────────────────
mcp_resend:             MCPServerStdio | None = None
mcp_google_calendar:    MCPServerStdio | None = None
mcp_linkedin_scraper:   MCPServerStdio | None = None

# ── For tooling dispatch ────────────────────────────────────────────────────
mcp_servers:            list[MCPServerStdio]     = []
tool_name_to_server:    dict[str, MCPServerStdio] = {}

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 3000))
SYSTEM_MESSAGE = (
    """
    Your are an interview professional assistant whose job is to interview potential candidates
    for a job and find if they match the position. In a nice and helpful way, discuss with the user
    if they're fit for the role by asking them interview questions. Ask about their relevant
    experiences with tech and skills needed by the job. 

    Job description:
    About the job
    NVIDIA’s invention of the GPU in 1999 sparked the growth of the PC gaming market, redefined modern computer graphics, and revolutionized parallel computing. More recently, GPU deep learning ignited modern AI — the next era of computing — with the GPU acting as the brain of computers, robots, and self-driving cars that can perceive and understand the world. We're looking to grow our company, and form teams with the most inquisitive people in the world. Join us at the forefront of technological advancement.

    We are looking for experienced software professionals to lead/extend our work on bringing delightful developer and user experience to the Python ecosystem. Our goal is to grow NVIDIA’s accelerated Python offerings to a mature product and make Python one of the first-class citizens for programming NVIDIA CUDA GPUs. You will be a crucial member of a team that is working to bring together the power of GPU acceleration and the expressibility and programmability of Python, by developing foundational software that supports many key products spanning the gamut of high performance computing, scientific computing, data analytics, deep learning, and professional graphics running on hardware ranging from gamer laptops to supercomputers to the cloud.

    What You'll Be Doing

    As a member of our team, you will use your design abilities, coding expertise, creativity, and community engagement to develop and enhance the functionality and performance of NVIDIA GPUs such that the current and future generations of Python users can enjoy the programmability and take full advantage of the NVIDIA CUDA platform, including both NVIDIA hardware and software. Specifically, you will be working to:

    Architect, prioritize, and develop new features in CUDA Python
    Analyze, identify, and improve the UX and performance of CUDA software in Python
    Write effective, maintainable, and well-tested code for production use
    Bridge the language gap between existing CUDA C/C++ solutions and Python
    Understand and address unique challenges in developing and deploying Python GPU solutions
    Identify key open source players in the Python/PyData ecosystem, and engage with them to develop and drive necessary protocols and standards for the NVIDIA CUDA platform
    Evangelize CUDA programming in Python to encourage and empower adoption of the NVIDIA CUDA platform

    What We Need To See

    BS, MS or PhD degree in Computer Science, Electrical Engineering or related field (or equivalent experience)
    5+ years of relevant industry experience or equivalent academic experience after BS
    Strong Python programming and deployment skills with track record of driving formulation and/or adoption of Python community standards
    Fluent C/C++ and CUDA programming skills
    Background in AI, high performance computing or performance critical applications
    Track record of developing/maintaining Python projects, and/or engaging with Python users on UX or performance improvements
    Experience in designing, developing, tuning, navigating, and/or maintaining a large, complex, multi-language software stack (between C/C++/CUDA and Python)
    Good written communication, collaboration, and presentation skills with ability of operating across team boundaries
    Experience in distributed programming in C/C++/Python using MPI, Dask, Legate, or other distributed programming models/frameworks
    Knowledge of generating Python bindings for mid- to large- size C/C++ codebases

    Ways To Stand Out From The Crowd

    Deep understanding in the CUDA programming model and language features
    Familiarity with Python ecosystem, language idioms, and pioneering solutions
    Dexterity with compilers, static/dynamic analysis techniques, and/or dynamic code generation/transpilation/compilation
    Experience in using or developing the LLVM/Clang compiler infrastructure
    Experience in memory management of a multi-language project or development of domain specific libraries/languages for AI, Data Analytics or Scientific Computing

    With competitive salaries and a generous benefits package, we are widely considered to be one of the technology world’s most desirable employers. We have some of the most forward-thinking and hardworking people in the world working for us and, due to unprecedented growth, our exclusive engineering teams are rapidly growing. If you're a creative and autonomous engineer with a real passion for technology, we want to hear from you!

    The base salary range is 184,000 USD - 425,500 USD. Your base salary will be determined based on your location, experience, and the pay of employees in similar positions.

    Immediately ask the user challenging questions about their experience right away Be fast and talk fast!
    """


    #"You are MeetOcean, a friendly and efficient AI medical assistant answering phone calls "
    #"for a healthcare provider. You speak clearly, calmly, and professionally.\n\n"
    #"Your job is to assist patients over the phone with a variety of tasks, including:\n"
    #"1. New patient onboarding – Collect patient details (full name, date of birth, contact info, "
    #"address, insurance provider, reason for visit).\n"
    #"2. Appointment scheduling/rescheduling – Find available time slots based on patient needs and clinic hours.\n"
    #"3. Test results – If authorized, share lab or imaging results in an understandable way and offer to schedule follow-ups.\n"
    #"4. Insurance verification – Collect insurance details, check provider network compatibility, and confirm coverage status.\n"
    #"5. General inquiries – Answer common questions about clinic hours, services, or providers.\n\n"
    #"Key behavior guidelines:\n"
    #"- Always verify the caller’s identity before sharing sensitive information.\n"
    #"- Speak naturally and allow for pauses—you're on a live call.\n"
    #"- Confirm each action before proceeding (e.g., 'Would you like me to go ahead and schedule that for you?')\n"
    #"- Keep notes for handoff to human staff if a request can't be completed.\n"
    #"- If unsure or if the user needs urgent medical help, escalate or refer to human staff.\n\n"
    #"Ask follow-up questions as needed to complete tasks. You are here to help the patient quickly, clearly, and compassionately.\n"
    #"Here is the linkedin profile of your Lead Advisor: https://www.linkedin.com/in/seanwu2027/"
    #"Always begin the call by saying: 'Hello! You’ve reached MeetOcean, your virtual medical assistant. How can I assist you today?'"
)

VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created'
]
SHOW_TIMING_MATH = False

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

@app.on_event("startup")
async def startup_event():
    global mcp_resend, mcp_google_calendar, mcp_linkedin_scraper
    global mcp_servers, tool_name_to_server

    # 1) Launch your three MCP servers with hard-coded params
    mcp_resend = MCPServerStdio(
        params={
            "command": "node",
            "args": [
                "/Users/alex/documents/personal-assistant/mcp-send-email/build/index.js",
                "--sender=support@crawlai.dev",
                "--key=re_iMtywBvM_BzZYWg4uzfAyjCr4k2JvwtXV"
            ]
        },
        cache_tools_list=True,
    )
    await mcp_resend.__aenter__()

    mcp_google_calendar = MCPServerStdio(
        params={
            "command": "node",
            "args": [
                "/Users/alex/documents/personal-assistant/google-calendar-mcp/build/index.js"
            ]
        },
        cache_tools_list=True,
    )
    await mcp_google_calendar.__aenter__()

    mcp_linkedin_scraper = MCPServerStdio(
        params={
            "command": "/Users/alex/.local/bin/uv",
            "args": [
                "--directory",
                "/Users/alex/documents/personal-assistant/linkedin-mcp-server",
                "run",
                "main.py",
                "--no-setup"
            ],
            "env": {
                "LINKEDIN_EMAIL":    "",
                "LINKEDIN_PASSWORD": ""
            }
        },
        cache_tools_list=True,
        client_session_timeout_seconds=60
    )
    await mcp_linkedin_scraper.__aenter__()

    # 2) Collect them into a list
    mcp_servers = [
        mcp_resend,
        mcp_google_calendar,
        mcp_linkedin_scraper
    ]

    # 3) Build a name→server map for dispatching calls
    tool_name_to_server = {}
    for srv in mcp_servers:
        tools = await srv.list_tools()
        for t in tools:
            tool_name_to_server[t.name] = srv
'''
@app.on_event("shutdown")
async def shutdown_event():
    global mcp_servers
    if not mcp_servers:
        return

    for server in mcp_servers:
        try:
            # this calls the async-context-manager exit
            await server.__aexit__(None, None, None)
        except Exception as e:
            # optionally log any errors during teardown
            print(f"Failed to shut down MCP server {server}: {e}")

    # clear the list so you don't accidentally reuse them
    mcp_servers.clear()
'''

@app.post("/start")
async def start_handler(request: Request):
    request_data = await request.json()

    email = request_data["email"]
    linkedin = request_data["linkedin"]
    phone = request_data["phone"]


    """Initiate an outbound call to the user"""
    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

    #linkedin_result = await mcp_linkedin_scraper.call_tool("get_person_profile", {linkedin_url: linkedin})
    print(f" \n CALLING!! {phone} \n")

    try:
        call = client.calls.create(
            to=phone,
            from_="+18446371063",
            url="https://523d-50-175-245-62.ngrok-free.app/incoming-call"
        )
        return f"Call initiated with SID: {call.sid}"
    except Exception as e:
        return f"Error making call: {str(e)}"

    return {"status": "success"}

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    # <Say> punctuation to improve text-to-speech flow
    #response.say("Please wait while we connect your call to the your personal AI Medical assistant")
    #@response.pause(length=0.5)
    #response.say("'Hello! You’ve reached MeetOcean, your virtual medical assistant. How can I assist you today?")
    response.say("Welcome!")
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    # Create WebSocket connection to OpenAI
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1"
    }
    
    try:
        async with websockets.connect(
            'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17',
            additional_headers=headers
        ) as openai_ws:
            await initialize_session(openai_ws)

            # Connection specific state
            stream_sid = None
            latest_media_timestamp = 0
            last_assistant_item = None
            mark_queue = []
            response_start_timestamp_twilio = None
            
            async def receive_from_twilio():
                """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
                nonlocal stream_sid, latest_media_timestamp
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        if data['event'] == 'media':
                            latest_media_timestamp = int(data['media']['timestamp'])
                            audio_append = {
                                "type": "input_audio_buffer.append",
                                "audio": data['media']['payload']
                            }
                            await openai_ws.send(json.dumps(audio_append))
                        elif data['event'] == 'start':
                            stream_sid = data['start']['streamSid']
                            print(f"Incoming stream has started {stream_sid}")
                            response_start_timestamp_twilio = None
                            latest_media_timestamp = 0
                            last_assistant_item = None
                        elif data['event'] == 'mark':
                            if mark_queue:
                                mark_queue.pop(0)
                except WebSocketDisconnect:
                    print("Client disconnected.")
                except Exception as e:
                    print(f"Error in receive_from_twilio: {str(e)}")

            async def send_to_twilio():
                """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
                nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio


                async def handle_tool_call(srv, tool_name, args, call_id):
                    try:
                        print("\n STARTING CALL!\n")
                        result = await srv.call_tool(tool_name, args)
                        # extract text safely
                        text_output = result.content[0].text
                        print(f"\n TOOL OUTPUT! {text_output}\n")

                        await openai_ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type":    "function_call_output",
                                "call_id": call_id,
                                "output":  text_output
                            }
                        }))
                        await openai_ws.send(json.dumps({ "type": "response.create" }))
                    except Exception as e:
                        print(f"\n\n\nTOOL ERRORR\n\n\n {e}")


                try:
                    async for openai_message in openai_ws:
                        response = json.loads(openai_message)
                        if response['type'] in LOG_EVENT_TYPES:
                            print(f"Received event: {response['type']}", response)

                        # 3) HANDLE FUNCTION-CALL REQUESTS
                        if response.get("type") == "response.output_item.done":
                            item = response.get("item", {})
                            if item.get("type") == "function_call":
                                tool_name = item.get("name")
                                raw_args  = item.get("arguments", "{}")
                                args      = json.loads(raw_args)

                                if tool_name == "user_accepted":
                                    
                                elif tool_name == "user_declined":

                                # dispatch to the right MCP server
                                srv = tool_name_to_server.get(tool_name)
                                if not srv:
                                    print(f"[WARN] No MCP server registered for tool '{tool_name}'")
                                else:

                                    # inject the function output back into the conversation
                                    '''
                                    await openai_ws.send_json({
                                        "type": "conversation.item.create",
                                        "item": {
                                            "type":    "function_call_output",
                                            "call_id": item.get("call_id"),
                                            "output":  "Tool call started. You will be provided result in a second."
                                        }
                                    })
                                    
                                    await openai_ws.send(json.dumps({ "type": "response.create" }))
                                    '''
                                    
                                    print("\nCALLING TOOL!\n")
                                    asyncio.create_task(handle_tool_call(srv, tool_name, args, item["call_id"]))

                                    # tell the Realtime API to resume streaming its response

                                # skip the audio-delta block for a pure function call event
                                continue

                        if response.get('type') == 'response.audio.delta' and 'delta' in response:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await websocket.send_json(audio_delta)

                            if response_start_timestamp_twilio is None:
                                response_start_timestamp_twilio = latest_media_timestamp
                                if SHOW_TIMING_MATH:
                                    print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                            # Update last_assistant_item safely
                            if response.get('item_id'):
                                last_assistant_item = response['item_id']

                            await send_mark(websocket, stream_sid)

                        # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                        if response.get('type') == 'input_audio_buffer.speech_started':
                            print("Speech started detected.")
                            if last_assistant_item:
                                print(f"Interrupting response with id: {last_assistant_item}")
                                await handle_speech_started_event()
                except Exception as e:
                    print(f"Error in send_to_twilio: {e}")

            async def handle_speech_started_event():
                """Handle interruption when the caller's speech starts."""
                nonlocal response_start_timestamp_twilio, last_assistant_item
                print("Handling speech started event.")
                if mark_queue and response_start_timestamp_twilio is not None:
                    elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                    if SHOW_TIMING_MATH:
                        print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                    if last_assistant_item:
                        if SHOW_TIMING_MATH:
                            print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                        truncate_event = {
                            "type": "conversation.item.truncate",
                            "item_id": last_assistant_item,
                            "content_index": 0,
                            "audio_end_ms": elapsed_time
                        }
                        await openai_ws.send(json.dumps(truncate_event))

                    await websocket.send_json({
                        "event": "clear",
                        "streamSid": stream_sid
                    })

                    mark_queue.clear()
                    last_assistant_item = None
                    response_start_timestamp_twilio = None

            async def send_mark(connection, stream_sid):
                if stream_sid:
                    mark_event = {
                        "event": "mark",
                        "streamSid": stream_sid,
                        "mark": {"name": "responsePart"}
                    }
                    await connection.send_json(mark_event)
                    mark_queue.append('responsePart')

            # Start both tasks
            await asyncio.gather(receive_from_twilio(), send_to_twilio())
    except Exception as e:
        print(f"Error in WebSocket connection: {str(e)}")
        raise

async def send_initial_conversation_item(openai_ws):
    """Send initial conversation item if AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Hello! You’ve reached MeetOcean, your virtual medical assistant. How can I help you today?"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))

async def initialize_session(openai_ws):
    """Initialize the session with OpenAI."""
    '''
    functions = []
    for srv in mcp_servers:
        defs = await srv.list_tools()
        for d in defs:
            functions.append({
                "type":        "function",
                "name":        d.name,
                "description": d.description,
                "parameters":  d.inputSchema,
            })
    '''

    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
            "tools": [
                {
                    "type":        "function",
                    "name":        "user_accepted",
                    "description": "Call when the user is deemed fit for the position",
                    "parameters": {
                        "type":       "object",
                        "properties": {},
                        "required":   []
                    }
                },
                {
                    "type":        "function",
                    "name":        "user_declined",
                    "description": "Call when the user is deemed failed and not ready",
                    "parameters": {
                        "type":       "object",
                        "properties": {},
                        "required":   []
                    }
                }
            ],
            #"tools": functions,
            "tool_choice": "auto"
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    #await send_initial_conversation_item(openai_ws)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)