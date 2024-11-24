import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, filedialog, PhotoImage
import time
import socket
import threading
from win10toast import ToastNotifier  # For Notifications



toaster = ToastNotifier()
# Track if dark mode is active
dark_mode = False

# Color themes for light and dark modes
light_theme = {
    "bg": "#FFFFFF",
    "fg": "#000000",
    "chat_bg": "#D8BFD8",
    "bubble_server": "#3c3c3c",
    "bubble_client": "#4CAF50",
    "entry_bg": "#3c3c3c",
    "entry_fg": "white",
    "button_bg": "#1E90FF",
    "button_fg": "white"
}

dark_theme = {
    "bg": "#2b2b2b",
    "fg": "#FFFFFF",
    "chat_bg": "#1e1e1e",
    "bubble_server": "#3c3c3c",
    "bubble_client": "#4CAF50",
    "entry_bg": "#555555",
    "entry_fg": "white",
    "button_bg": "#007acc",
    "button_fg": "white"
}


    
def apply_theme(root, theme):
    root.configure(bg=theme["bg"])
    header_frame.configure(bg=theme["chat_bg"])
    chat_frame.configure(bg=theme["chat_bg"])
    message_frame.configure(bg=theme["chat_bg"])
    search_frame.configure(bg=theme["bg"])
    message_entry.configure(bg=theme["entry_bg"], fg=theme["entry_fg"])
    send_button.configure(bg=theme["button_bg"], fg=theme["button_fg"])
    logout_button.configure(bg="#f44336", fg="white")
    search_label.configure(bg=theme["bg"], fg=theme["fg"])
    search_entry.configure(bg=theme["entry_bg"], fg=theme["entry_fg"])

def show_splash_screen():
    """Displays a splash screen with the Echo logo for 3 seconds."""
    splash = tk.Tk()
    splash.title("Echo")
    splash.geometry("500x300")
    splash.configure(bg="#FFFFFF")

    # Load the logo image
    logo_image = PhotoImage(file="echo_logo.png")
    logo_label = tk.Label(splash, image=logo_image, bg="#FFFFFF")
    logo_label.image = logo_image  # Keep a reference to avoid garbage collection
    logo_label.pack(expand=True)

    # Center the splash screen on the screen
    splash.update_idletasks()
    width = splash.winfo_width()
    height = splash.winfo_height()
    x = (splash.winfo_screenwidth() // 2) - (width // 2)
    y = (splash.winfo_screenheight() // 2) - (height // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")

    # Keep the splash screen open for 3 seconds
    splash.after(3000, splash.destroy)
    splash.mainloop()

def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    theme = dark_theme if dark_mode else light_theme
    apply_theme(root, theme)

def receive_messages(client_socket, chat_frame):
    while True:
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if msg:
                add_chat_bubble(chat_frame, msg, "server")
                show_notification("New Message", msg)  # Display Windows notification for each new message
        except:
            break

def show_notification(title, message): #Function to display Windows notifications using win10toast.
    toaster.show_toast(
        title=title,
        msg=message,
        duration=5,
        threaded=True
    )
def send_message(client_socket, message_entry, chat_frame):
    msg = message_entry.get()
    if msg.strip():
        client_socket.send(msg.encode('utf-8'))
        add_chat_bubble(chat_frame, msg, "client")
        message_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Echo", "Cannot send empty message")

def create_custom_dialog(title, prompt, is_password=False): #Function for user authentication
    dialog = tk.Toplevel()
    dialog.title(f"Echo - Authenticate yourself {title}")
    dialog.geometry("655x405")
    dialog.configure(bg="#FFFFFF")
    
    prompt_label = tk.Label(dialog, text=prompt, bg="#FFFFFF", fg="#4B0082", font=("Helvetica", 12))
    prompt_label.pack(pady=10)

    entry = tk.Entry(dialog, bg="#3c3c3c", fg="white", font=("Helvetica", 12), show="*" if is_password else "")
    entry.pack(pady=5)

    def on_submit():
        dialog.result = entry.get()
        dialog.destroy()

    submit_button = tk.Button(dialog, text="Submit", bg="#9370DB", fg="#FFFFFF", font=("Helvetica", 12, "bold"), command=on_submit)
    submit_button.pack(pady=10)

    dialog.grab_set()
    dialog.wait_window()

    return getattr(dialog, 'result', None)

def logout(client_socket, root): #Logout function
    client_socket.close()
    root.destroy()

def add_chat_bubble(chat_frame, message, sender):
    theme = dark_theme if dark_mode else light_theme
    bubble_frame = tk.Frame(chat_frame, bg=theme["chat_bg"])
    bubble_frame.pack(fill=tk.X, pady=5, padx=10, anchor='w' if sender == "server" else 'e')

    bubble_bg = theme["bubble_server"] if sender == "server" else theme["bubble_client"]
    bubble = tk.Label(
        bubble_frame, text=message, bg=bubble_bg, fg="white", font=("Helvetica", 12), 
        wraplength=250, justify=tk.LEFT if sender == "server" else tk.RIGHT, 
        anchor='w' if sender == "server" else 'e', padx=10, pady=5
    )
    bubble.pack(side=tk.LEFT if sender == "server" else tk.RIGHT, fill=tk.X)

def search_messages(chat_frame, search_entry): #function to search messages.
    search_term = search_entry.get().lower()
    for bubble_frame in chat_frame.winfo_children():
        bubble_label = bubble_frame.winfo_children()[0]
        text = bubble_label.cget("text").lower()
        if search_term in text:
            bubble_label.config(bg="#FFD700")
        else:
            if "server" in bubble_label.cget("anchor"):
                bubble_label.config(bg="#3c3c3c")
            else:
                bubble_label.config(bg="#4CAF50")

def start_client(): #Main function
    show_splash_screen()
    
    global root, header_frame, chat_frame, message_frame, message_entry, send_button, logout_button, search_frame, search_label, search_entry

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("localhost", 9999))


    root = tk.Tk()
    root.title("Echo - Client")
    root.state('zoomed')
    root.configure(bg="#FFFFFF")


    #GUI
    header_frame = tk.Frame(root, bg="#D8BFD8")
    header_frame.pack(pady=10, fill=tk.X)

    header = tk.Label(header_frame, text="Echo", bg="#D8BFD8", fg="black", font=("Helvetica", 16, "bold"))
    header.pack(side=tk.LEFT, padx=(10, 0))

    logout_button = tk.Button(header_frame, text=" Log Out ", bg="#f44336", fg="white", font=("Helvetica", 12, "bold"), command=lambda: logout(client_socket, root))
    logout_button.pack(side=tk.RIGHT, padx=(0, 10))

    dark_mode_button = tk.Button(header_frame, text=" Theme ", font=("Helvetica", 12), command=toggle_dark_mode)
    dark_mode_button.pack(side=tk.RIGHT, padx=(0, 10))

    chat_frame = tk.Frame(root, bg="#D8BFD8")
    chat_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    message_frame = tk.Frame(root, bg="#D8BFD8")
    message_frame.pack(pady=5, padx=10, fill=tk.X)

    message_entry = tk.Entry(message_frame, bg="#3c3c3c", fg="white", font=("Helvetica", 12))
    message_entry.pack(side=tk.LEFT, pady=5, padx=(0, 5), fill=tk.X, expand=True)

    send_button = tk.Button(message_frame, text=">", bg="#1E90FF", fg="white", font=("Helvetica", 12, "bold"), 
                            command=lambda: send_message(client_socket, message_entry, chat_frame))
    send_button.pack(side=tk.RIGHT, pady=5)
    #search
    search_frame = tk.Frame(root, bg="#2b2b2b")
    search_frame.pack(pady=5)

    search_label = tk.Label(search_frame, text="Search Messages:", bg="#2b2b2b", fg="white", font=("Helvetica", 12))
    search_label.pack(side=tk.LEFT, padx=(5, 2))

    search_entry = tk.Entry(search_frame, bg="#3c3c3c", fg="white", font=("Helvetica", 12))
    search_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

    search_button = tk.Button(search_frame, text="Search", bg="#4CAF50", fg="white", font=("Helvetica", 12), 
                              command=lambda: search_messages(chat_frame, search_entry))
    search_button.pack(side=tk.RIGHT, padx=(0, 5))
    apply_theme(root, light_theme)

    threading.Thread(target=receive_messages, args=(client_socket, chat_frame), daemon=True).start()

    root.mainloop()
    client_socket.close()

if __name__ == "__main__":
    start_client()
