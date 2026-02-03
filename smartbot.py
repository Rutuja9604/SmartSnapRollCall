import tkinter as tk

def open_smartbot(parent):

    bot = tk.Toplevel(parent)
    bot.title("🤖 SmartBot Assistant")
    bot.geometry("400x500")
    bot.configure(bg="#0f1720")

    chat_area = tk.Text(bot, bg="#1e293b", fg="white", font=("Segoe UI", 11), wrap="word")
    chat_area.pack(padx=10, pady=10, fill="both", expand=True)
    chat_area.insert("end", "🤖 SmartBot: Hello! I am your attendance assistant. How can I help you?\n\n")

    entry = tk.Entry(bot, font=("Segoe UI", 12))
    entry.pack(padx=10, pady=10, fill="x")

    def get_reply(msg):
        msg = msg.lower()

        # ADMIN
        if "add student" in msg:
            return "To add student, go to Admin Panel → Add Student."

        if "add teacher" in msg:
            return "To add teacher, go to Admin Panel → Add Teacher."

        # TEACHER
        if "take attendance" in msg:
            return "Go to Teacher Dashboard → Upload Group Photo."

        # STUDENT
        if "my attendance" in msg:
            return "Go to Student Dashboard → Overall Attendance."

        if "percentage" in msg:
            return "Your attendance percentage is shown in the dashboard."

        if "hello" in msg or "hi" in msg:
            return "Hello 👋 How can I help you today?"

        return "Sorry 😅 I didn't understand. Try asking about attendance, students or teachers."

    def send_message():
        user_msg = entry.get()
        if user_msg.strip() == "":
            return

        chat_area.insert("end", f"🧑 You: {user_msg}\n")
        reply = get_reply(user_msg)
        chat_area.insert("end", f"🤖 SmartBot: {reply}\n\n")
        chat_area.see("end")
        entry.delete(0, "end")

    send_btn = tk.Button(bot, text="Send", bg="#08bdb6", fg="black", font=("Segoe UI", 11, "bold"),
                          command=send_message)
    send_btn.pack(pady=5)
