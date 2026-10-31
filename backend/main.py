from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.gemini_service import GeminiService

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

SERVICE = GeminiService()


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2)
    email: str
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: str
    password: str = Field(..., min_length=6)


class EventCreate(BaseModel):
    event_name: str
    event_type: str
    event_date: str
    location: str
    guest_count: int = Field(..., ge=1)
    total_budget: int = Field(..., ge=1)
    currency: str = 'INR'
    theme: str = ''
    event_style: str = 'Modern'
    event_description: str = ''


class BudgetItem(BaseModel):
    category: str
    estimated_amount: float = 0
    actual_amount: float = 0
    notes: str = ''


class TaskItem(BaseModel):
    task_name: str
    category: str
    description: str = ''
    deadline: str | None = None
    priority: str = 'Medium'
    status: str = 'Pending'


class VendorItem(BaseModel):
    vendor_name: str
    category: str
    contact_number: str = ''
    email: str = ''
    website: str = ''
    quoted_price: float = 0
    booking_status: str = 'Not Contacted'
    notes: str = ''


class ChatRequest(BaseModel):
    message: str
    event_id: str | None = None
    context: dict[str, Any] | None = None


DEMO_USERS = {
    'demo@example.com': {'id': 'demo-user', 'full_name': 'Demo User', 'email': 'demo@example.com', 'password': 'demo123'}
}

DEMO_EVENTS: dict[str, dict[str, Any]] = {}


def _ensure_demo_event():
    if not DEMO_EVENTS:
        DEMO_EVENTS['event-demo-1'] = {
            'id': 'event-demo-1',
            'user_id': 'demo-user',
            'event_name': 'Royal Birthday Celebration',
            'event_type': 'Birthday',
            'event_date': '2026-11-15',
            'location': 'Mumbai, India',
            'guest_count': 50,
            'total_budget': 50000,
            'currency': 'INR',
            'theme': 'Luxury Golden Theme',
            'event_style': 'Luxury',
            'event_description': 'Premium birthday celebration for family and friends.',
            'budgets': [
                {'id': 'b1', 'category': 'Venue', 'estimated_amount': 15000, 'actual_amount': 14000, 'notes': 'Garden hall booking'},
                {'id': 'b2', 'category': 'Catering', 'estimated_amount': 12000, 'actual_amount': 11000, 'notes': 'Veg and non-veg buffet'},
            ],
            'tasks': [
                {'id': 't1', 'task_name': 'Finalize venue', 'category': 'Planning', 'description': 'Confirm venue contract', 'deadline': '2026-11-01', 'priority': 'High', 'status': 'Completed'},
                {'id': 't2', 'task_name': 'Send invites', 'category': 'Invitations', 'description': 'Mail RSVP reminder', 'deadline': '2026-11-05', 'priority': 'Medium', 'status': 'Pending'},
            ],
            'vendors': [
                {'id': 'v1', 'vendor_name': 'Chandra Events', 'category': 'Decoration', 'contact_number': '+91 98765 43210', 'email': 'hello@chandraevents.in', 'website': 'https://example.com', 'quoted_price': 18000, 'booking_status': 'Confirmed', 'notes': 'Sample vendor record'}
            ],
            'checklist': [
                {'id': 'c1', 'task_name': 'Confirm guest list', 'status': 'Completed'},
                {'id': 'c2', 'task_name': 'Arrange floral décor', 'status': 'Pending'},
            ],
            'recommendations': [
                {'id': 'r1', 'recommendation_type': 'Theme', 'content': 'Use warm golden lighting and layered florals to create a royal stage backdrop.'},
            ],
            'chat_history': [],
        }


def _serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    event = dict(event)
    event['budgets'] = event.get('budgets', [])
    event['tasks'] = event.get('tasks', [])
    event['vendors'] = event.get('vendors', [])
    event['checklist'] = event.get('checklist', [])
    event['recommendations'] = event.get('recommendations', [])
    event['chat_history'] = event.get('chat_history', [])
    return event


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_demo_event()
    yield


app = FastAPI(title='EventEase AI API', version='1.0.0', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.post('/api/auth/register')
async def register_user(payload: UserCreate):
    email = payload.email.lower().strip()
    if email in DEMO_USERS:
        raise HTTPException(status_code=400, detail='User already exists.')
    user = {
        'id': f'user-{uuid.uuid4().hex[:8]}',
        'full_name': payload.full_name,
        'email': email,
        'password': payload.password,
    }
    DEMO_USERS[email] = user
    return {'message': 'Registration successful', 'user': {'id': user['id'], 'full_name': user['full_name'], 'email': user['email']}}


@app.post('/api/auth/login')
async def login_user(payload: UserLogin):
    email = payload.email.lower().strip()
    user = DEMO_USERS.get(email)
    if not user or user['password'] != payload.password:
        raise HTTPException(status_code=401, detail='Invalid email or password.')
    return {'message': 'Login successful', 'user': {'id': user['id'], 'full_name': user['full_name'], 'email': user['email']}, 'token': 'demo-token'}


@app.get('/api/events')
async def get_events() -> list[dict[str, Any]]:
    return [_serialize_event(event) for event in DEMO_EVENTS.values()]


@app.post('/api/events')
async def create_event(payload: EventCreate):
    event_id = f'event-{uuid.uuid4().hex[:8]}'
    event = {
        'id': event_id,
        'user_id': 'demo-user',
        'event_name': payload.event_name,
        'event_type': payload.event_type,
        'event_date': payload.event_date,
        'location': payload.location,
        'guest_count': payload.guest_count,
        'total_budget': payload.total_budget,
        'currency': payload.currency,
        'theme': payload.theme or 'Elegant Modern Theme',
        'event_style': payload.event_style,
        'event_description': payload.event_description,
        'budgets': [],
        'tasks': [],
        'vendors': [],
        'checklist': [],
        'recommendations': [],
        'chat_history': [],
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
    }
    DEMO_EVENTS[event_id] = event
    return _serialize_event(event)


@app.get('/api/events/{event_id}')
async def get_event(event_id: str):
    event = DEMO_EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found.')
    return _serialize_event(event)


@app.put('/api/events/{event_id}')
async def update_event(event_id: str, payload: dict[str, Any]):
    event = DEMO_EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found.')
    for key, value in payload.items():
        if key in {'id', 'user_id'}:
            continue
        event[key] = value
    event['updated_at'] = datetime.utcnow().isoformat()
    return _serialize_event(event)


@app.delete('/api/events/{event_id}')
async def delete_event(event_id: str):
    if event_id not in DEMO_EVENTS:
        raise HTTPException(status_code=404, detail='Event not found.')
    del DEMO_EVENTS[event_id]
    return {'message': 'Event deleted'}


@app.post('/api/ai/generate-plan')
async def generate_plan(payload: dict[str, Any]):
    event_data = payload.get('event', payload)
    plan = SERVICE.generate_event_plan(event_data)
    event_id = payload.get('event_id')
    if event_id and event_id in DEMO_EVENTS:
        DEMO_EVENTS[event_id]['recommendations'] = [{'id': f'r-{uuid.uuid4().hex[:6]}', 'recommendation_type': 'Plan', 'content': json.dumps(plan, ensure_ascii=False)}]
    return plan


@app.post('/api/ai/chat')
async def chat(payload: ChatRequest):
    response = SERVICE.chat_with_event_assistant(payload.message, payload.context or {})
    if payload.event_id and payload.event_id in DEMO_EVENTS:
        DEMO_EVENTS[payload.event_id]['chat_history'].append({'role': 'user', 'message': payload.message, 'created_at': datetime.utcnow().isoformat()})
        DEMO_EVENTS[payload.event_id]['chat_history'].append({'role': 'assistant', 'message': response.get('answer', ''), 'created_at': datetime.utcnow().isoformat()})
    return response


@app.post('/api/ai/generate-themes')
async def generate_themes(payload: dict[str, Any]):
    return SERVICE.generate_theme_recommendations(payload)


@app.post('/api/ai/generate-timeline')
async def generate_timeline(payload: dict[str, Any]):
    return SERVICE.generate_event_timeline(payload)


@app.post('/api/ai/optimize-budget')
async def optimize_budget(payload: dict[str, Any]):
    return SERVICE.optimize_event_budget(payload)


@app.get('/api/events/{event_id}/budget')
async def get_budget(event_id: str):
    event = DEMO_EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found.')
    return {'items': event.get('budgets', [])}


@app.post('/api/events/{event_id}/budget')
async def add_budget_item(event_id: str, payload: BudgetItem):
    event = DEMO_EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found.')
    item = {
        'id': f'b-{uuid.uuid4().hex[:6]}',
        'category': payload.category,
        'estimated_amount': payload.estimated_amount,
        'actual_amount': payload.actual_amount,
        'notes': payload.notes,
    }
    event.setdefault('budgets', []).append(item)
    return item


@app.put('/api/budget/{budget_id}')
async def update_budget_item(budget_id: str, payload: BudgetItem):
    for event in DEMO_EVENTS.values():
        for item in event.get('budgets', []):
            if item['id'] == budget_id:
                item.update({
                    'category': payload.category,
                    'estimated_amount': payload.estimated_amount,
                    'actual_amount': payload.actual_amount,
                    'notes': payload.notes,
                })
                return item
    raise HTTPException(status_code=404, detail='Budget item not found.')


@app.delete('/api/budget/{budget_id}')
async def delete_budget_item(budget_id: str):
    for event in DEMO_EVENTS.values():
        items = event.get('budgets', [])
        for idx, item in enumerate(items):
            if item['id'] == budget_id:
                del items[idx]
                return {'message': 'Budget item removed'}
    raise HTTPException(status_code=404, detail='Budget item not found.')


@app.get('/api/events/{event_id}/tasks')
async def get_tasks(event_id: str):
    event = DEMO_EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found.')
    return {'items': event.get('tasks', [])}


@app.post('/api/events/{event_id}/tasks')
async def add_task(event_id: str, payload: TaskItem):
    event = DEMO_EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found.')
    task = {
        'id': f't-{uuid.uuid4().hex[:6]}',
        'task_name': payload.task_name,
        'category': payload.category,
        'description': payload.description,
        'deadline': payload.deadline,
        'priority': payload.priority,
        'status': payload.status,
    }
    event.setdefault('tasks', []).append(task)
    return task


@app.put('/api/tasks/{task_id}')
async def update_task(task_id: str, payload: TaskItem):
    for event in DEMO_EVENTS.values():
        for task in event.get('tasks', []):
            if task['id'] == task_id:
                task.update({
                    'task_name': payload.task_name,
                    'category': payload.category,
                    'description': payload.description,
                    'deadline': payload.deadline,
                    'priority': payload.priority,
                    'status': payload.status,
                })
                return task
    raise HTTPException(status_code=404, detail='Task not found.')


@app.delete('/api/tasks/{task_id}')
async def delete_task(task_id: str):
    for event in DEMO_EVENTS.values():
        tasks = event.get('tasks', [])
        for idx, task in enumerate(tasks):
            if task['id'] == task_id:
                del tasks[idx]
                return {'message': 'Task deleted'}
    raise HTTPException(status_code=404, detail='Task not found.')


@app.get('/api/events/{event_id}/vendors')
async def get_vendors(event_id: str):
    event = DEMO_EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found.')
    return {'items': event.get('vendors', [])}


@app.post('/api/events/{event_id}/vendors')
async def add_vendor(event_id: str, payload: VendorItem):
    event = DEMO_EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found.')
    vendor = {
        'id': f'v-{uuid.uuid4().hex[:6]}',
        'vendor_name': payload.vendor_name,
        'category': payload.category,
        'contact_number': payload.contact_number,
        'email': payload.email,
        'website': payload.website,
        'quoted_price': payload.quoted_price,
        'booking_status': payload.booking_status,
        'notes': payload.notes,
    }
    event.setdefault('vendors', []).append(vendor)
    return vendor


@app.put('/api/vendors/{vendor_id}')
async def update_vendor(vendor_id: str, payload: VendorItem):
    for event in DEMO_EVENTS.values():
        for vendor in event.get('vendors', []):
            if vendor['id'] == vendor_id:
                vendor.update({
                    'vendor_name': payload.vendor_name,
                    'category': payload.category,
                    'contact_number': payload.contact_number,
                    'email': payload.email,
                    'website': payload.website,
                    'quoted_price': payload.quoted_price,
                    'booking_status': payload.booking_status,
                    'notes': payload.notes,
                })
                return vendor
    raise HTTPException(status_code=404, detail='Vendor not found.')


@app.delete('/api/vendors/{vendor_id}')
async def delete_vendor(vendor_id: str):
    for event in DEMO_EVENTS.values():
        vendors = event.get('vendors', [])
        for idx, vendor in enumerate(vendors):
            if vendor['id'] == vendor_id:
                del vendors[idx]
                return {'message': 'Vendor removed'}
    raise HTTPException(status_code=404, detail='Vendor not found.')


@app.get('/api/events/{event_id}/report')
async def generate_report(event_id: str):
    event = DEMO_EVENTS.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found.')
    return {
        'event_id': event_id,
        'generated_at': datetime.utcnow().isoformat(),
        'event_name': event['event_name'],
        'theme': event['theme'],
        'budget': sum(item.get('estimated_amount', 0) for item in event.get('budgets', [])),
        'summary': f'{event["event_name"]} is planned with a {event["theme"]} experience and a balanced budget focus.',
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)
