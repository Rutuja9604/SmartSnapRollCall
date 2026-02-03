from django.shortcuts import render
from django.http import JsonResponse

def chat_view(request):
    if request.method == "POST":
        user_msg = request.POST.get("message")
        reply = get_bot_reply(user_msg)
        return JsonResponse({"reply": reply})

    return render(request, "chatbot/chat.html")


def get_bot_reply(message):
    msg = message.lower()

    # ---- GREETINGS ----
    if "hi" in msg or "hello" in msg:
        return "Hello 👋 I’m SmartBot. How can I assist you with attendance today?"

    # ---- ADMIN ----
    if "add student" in msg:
        return "To add a student, go to Admin Panel → Manage Students → Add Student."

    if "add teacher" in msg:
        return "To add a teacher, go to Admin Panel → Manage Teachers → Add Teacher."

    if "delete student" in msg:
        return "You can delete a student from Admin Panel → Manage Students."

    # ---- TEACHER ----
    if "take attendance" in msg or "mark attendance" in msg:
        return "To take attendance, open Teacher Dashboard and upload the group photo."

    if "upload photo" in msg:
        return "Use the 'Upload Group Photo' option in Teacher Dashboard."

    # ---- STUDENT ----
    if "my attendance" in msg:
        return "You can view your attendance in Student Dashboard → Overall Attendance."

    if "percentage" in msg:
        return "Your attendance percentage is displayed in the Student Dashboard."

    if "absent" in msg:
        return "If you were absent, contact your subject teacher for clarification."

    # ---- GENERAL ----
    if "help" in msg:
        return "I can help you with attendance, students, teachers, admin tasks and more."

    return "🤖 Sorry, I didn’t understand that. You can ask about attendance, students, teachers, or admin."
