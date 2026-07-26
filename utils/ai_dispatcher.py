import math
from models import db
from models.user import User
from models.worker import WorkerProfile
from models.complaint import Complaint
from datetime import datetime, timezone

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees)"""
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
        
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

def auto_assign_complaint(complaint_id, max_radius_km=25.0):
    """
    Finds the best worker based on distance, role, and workload.
    """
    complaint = Complaint.query.get(complaint_id)
    if not complaint:
        return False, "Complaint not found."
        
    if not complaint:
        return False, "Complaint not found."

    # Find all available workers
    available_workers_query = db.session.query(User).join(WorkerProfile).filter(
        User.role == "worker",
        WorkerProfile.is_available == True
    )

    all_available_workers = available_workers_query.all()

    if not all_available_workers:
        return False, "No available workers with GPS location found."

    # Map complaint categories to preferred designations
    category_designation_map = {
        "power_outage": ["Line Worker", "Lineman", "Electrician"],
        "voltage_issue": ["Electrician", "Line Worker"],
        "meter_problem": ["Meter Technician", "Meter Reader"],
        "billing": ["Meter Technician", "Meter Reader"],
    }
    
    preferred_keywords = category_designation_map.get(complaint.category, [])
    
    # Filter preferred workers first if possible
    workers = []
    if preferred_keywords:
        for w in all_available_workers:
            desig = (w.worker_profile.designation or "").lower()
            if any(kw.lower() in desig for kw in preferred_keywords):
                workers.append(w)
                
    # Fallback to all available workers if no preferred role match found
    if not workers:
        workers = all_available_workers

    best_worker = None
    lowest_workload = float('inf')
    closest_distance = float('inf')

    for w in workers:
        # 1. Check distance
        has_gps = complaint.latitude is not None and w.worker_profile.latitude is not None
        if has_gps:
            dist = haversine(complaint.latitude, complaint.longitude, w.worker_profile.latitude, w.worker_profile.longitude)
        else:
            # Fallback to section matching if no GPS
            if complaint.location and w.worker_profile.section and w.worker_profile.section.lower() in complaint.location.lower():
                dist = 5.0 # assume 5km if sections match
            else:
                dist = 20.0 # assume 20km otherwise
        
        if dist <= max_radius_km:
            # 2. Check workload
            active_jobs = Complaint.query.filter(
                Complaint.assigned_worker_id == w.id,
                Complaint.status.in_(["assigned", "in_progress"])
            ).count()
            
            # 3. Decision logic: prioritize lowest workload. If tied, pick closest.
            if active_jobs < lowest_workload:
                lowest_workload = active_jobs
                best_worker = w
                closest_distance = dist
            elif active_jobs == lowest_workload and dist < closest_distance:
                best_worker = w
                closest_distance = dist

    if best_worker:
        # Assign!
        complaint.assigned_worker_id = best_worker.id
        complaint.status = "assigned"
        complaint.updated_at = datetime.now(timezone.utc)
        
        # Create a notification for the worker
        from models.notification import Notification
        notif = Notification(
            user_id=best_worker.id,
            complaint_id=complaint.id,
            title=f"New Job Assigned #{complaint.id}",
            message=f"Complaint #{complaint.id}: '{complaint.title}' at {complaint.location} has been assigned to you. Distance: {closest_distance:.1f}km."
        )
        db.session.add(notif)
        
        db.session.commit()
        
        return True, f"Auto-assigned to {best_worker.name} (Distance: {closest_distance:.1f}km, Active Jobs: {lowest_workload}). Notification sent to {best_worker.phone}!"
    
    return False, f"No available workers found within {max_radius_km}km radius."
