import sys
import os
import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.models import chat_with_llama
from backend.database import get_all_requests, get_all_responders

def match_responders_to_requests():
    """
    Match active responders and volunteers to pending requests using LLaMA model.
    
    Returns:
        dict: Mapping of request IDs to matched responders with action plans
    """
    # Get all active requests that are pending
    requests_response = get_all_requests()
    if "error" in requests_response:
        return {"error": f"Failed to fetch requests: {requests_response['error']}"}
    
    pending_requests = [r for r in requests_response.get("data", []) if r.get("status") == "pending"]
    
    # Get all active responders and volunteers
    responders_response = get_all_responders()
    if "error" in responders_response:
        return {"error": f"Failed to fetch responders: {responders_response['error']}"}
    
    active_responders = [r for r in responders_response.get("data", []) 
                        if r.get("user_status") == "active"]
    
    # No pending requests or active responders
    if not pending_requests or not active_responders:
        return {"message": "No pending requests or active responders found", "matches": {}}
    
    # Create a map of request ID to matched responders
    matches = {}
    
    # For each pending request, find matching responders
    for request in pending_requests:
        request_id = request.get("id")
        request_text = request.get("text", "")
        request_type = request.get("type", "")
        request_urgency = request.get("urgency", "Medium")
        request_location = request.get("location", "")
        
        # Format responders data for LLaMA prompt
        responders_data = "\n\n".join([
            f"Responder ID: {resp.get('id')}\n"
            f"Name: {resp.get('fullName', 'Unknown')}\n"
            f"Role: {resp.get('role', 'volunteer')}\n"
            f"Skills: {resp.get('skills', 'None')}\n"
            f"Specialties: {resp.get('specialties', 'None')}\n"
            f"Experience: {resp.get('experience', 'beginner')}\n"
            f"Location: {resp.get('location', 'Unknown')}\n"
            for resp in active_responders
        ])
        
        # Create prompt for LLaMA to match responders to this request
        matching_prompt = f"""
        You are an emergency response coordinator. Match the best responders to this emergency request.
        
        REQUEST DETAILS:
        ID: {request_id}
        Type: {request_type}
        Description: {request_text}
        Urgency: {request_urgency}
        Location: {request_location}
        
        AVAILABLE RESPONDERS:
        {responders_data}
        
        Analyze the request and available responders. Choose the 3 best matches based on:
        1. Skills and specialties relevant to the request
        2. Experience level appropriate for the urgency
        3. Role suitability (first responders for high urgency)
        
        For each match, provide a brief action plan with instructions on how to handle this request.
        
        Return your response as a Python dictionary with this exact format:
        {{
            "matches": [
                {{"responder_id": "ID1", "match_reason": "Reason for match", "action_plan": "Specific instructions"}},
                {{"responder_id": "ID2", "match_reason": "Reason for match", "action_plan": "Specific instructions"}},
                {{"responder_id": "ID3", "match_reason": "Reason for match", "action_plan": "Specific instructions"}}
            ]
        }}
        
        Only return a valid Python dictionary. No other text or explanation.
        """
        
        # Query LLaMA for matches
        try:
            response = chat_with_llama(matching_prompt)
            
            # Extract the dictionary from the response
            import re
            import json
            
            # Find dictionary pattern in the response
            dict_pattern = r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}'
            dict_match = re.search(dict_pattern, response)
            
            if dict_match:
                dict_str = dict_match.group(0)
                try:
                    # Parse the dictionary
                    match_data = json.loads(dict_str)
                    matches[request_id] = match_data
                except json.JSONDecodeError:
                    matches[request_id] = {"error": "Failed to parse LLaMA response", "raw": response}
            else:
                matches[request_id] = {"error": "No valid dictionary found in response", "raw": response}
                
        except Exception as e:
            matches[request_id] = {"error": str(e)}
    
    return {"matches": matches}