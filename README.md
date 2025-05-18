# AI Interview Assistant

An automated phone interview system powered by Twilio and AI that verifies candidates' credentials against their LinkedIn profiles.

## Overview

This project combines:

* Automated outbound calls using Twilio
* AI-powered conversation using OpenAI's Realtime API
* LinkedIn profile verification
* Next.js frontend for candidate information collection

## Project Structure

### Backend (Python)

* **`agent.py`**: Core FastAPI application handling Twilio Stream API and OpenAI integration

### Frontend (Next.js)

A modern React application for collecting candidate information:

* Form fields: Email, LinkedIn profile URL, and phone number
* Built with Next.js, React, and Tailwind CSS
* Responsive design with professional styling

## Features

* AI-powered phone interviews
* LinkedIn profile verification
* Automated outbound calling
* Real-time conversation processing
* Responsive web form for candidate information

## Dependencies

### Backend

* FastAPI/Uvicorn
* Twilio
* python-dotenv
* websockets
* python-multipart

### Frontend

* Next.js
* React
* Radix UI components
* Tailwind CSS
* React Hook Form
* Zod
* TypeScript
