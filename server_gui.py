import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, Listbox, filedialog, PhotoImage
import socket
import threading
import queue
from user_auth import register_user, login_user
groups = {}  # Dictionary to store groups and their members
active_users = {}  # Dictionary to store active users with client_socket as the key and username as the value

def handle_client(client_socket, chat_display, user_list, username):
    while True:
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if msg:
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, f"{username}: {msg}\n")
                chat_display.config(state=tk.DISABLED)
            else:
                break
        except:
            break
    user_list.delete(user_list.get(0, tk.END).index(username))
    client_socket.close()

def send_message(client_socket, message_entry, username, chat_display):
    msg = message_entry.get()
    client_socket.send(msg.encode('utf-8'))
    message_entry.delete(0, tk.END)
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(tk.END, f"You: {msg}\n")
    chat_display.config(state=tk.DISABLED)

def handle_client(client_socket, chat_display, user_list, username):
    user_group = None  # Variable to store the user's group

    while True:
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if msg:
                # Check for group-specific messages
                if msg.startswith("/join_group"):
                    group_name = msg.split()[1]
                    response = join_group(group_name, client_socket)
                    client_socket.send(response.encode())
                    user_group = group_name if "successfully" in response else None

                elif user_group:  # If the user is in a group, broadcast the message
                    for member_socket in groups[user_group]:
                        if member_socket != client_socket:  # Avoid sending to self
                            member_socket.send(f"{username} (in {user_group}): {msg}".encode())
                else:
                    # Standard message handling for individual chat
                    chat_display.config(state=tk.NORMAL)
                    chat_display.insert(tk.END, f"{username}: {msg}\n")
                    chat_display.config(state=tk.DISABLED)

            else:
                break
        except:
            break

    if client_socket in active_users:
        del active_users[client_socket]

    user_list.delete(user_list.get(0, tk.END).index(username))
    client_socket.close()



def create_custom_dialog(title, prompt, is_password=False):
    dialog = tk.Toplevel()
    dialog.title(title)
    dialog.geometry("300x150")
    dialog.configure(bg="#2b2b2b")
    
    prompt_label = tk.Label(dialog, text=prompt, bg="#2b2b2b", fg="white", font=("Helvetica", 12))
    prompt_label.pack(pady=10)

    entry = tk.Entry(dialog, bg="#3c3c3c", fg="white", font=("Helvetica", 12), show="*" if is_password else "")
    entry.pack(pady=5)

    def on_submit():
        dialog.result = entry.get()
        dialog.destroy()

    submit_button = tk.Button(dialog, text="Submit", bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"), command=on_submit)
    submit_button.pack(pady=10)

    dialog.grab_set()
    dialog.wait_window()

    return getattr(dialog, 'result', None)

def create_group_prompt():
    group_name = create_custom_dialog("Create Group", "Enter Group Name:")
    if group_name:
        response = create_group(group_name, None)  # None for server-side group creation
        messagebox.showinfo("Echo", response)

def join_group_prompt():
    group_name = create_custom_dialog("Join Group", "Enter Group Name:")
    if group_name:
        response = join_group(group_name, None)  # None for server-side group joining
        messagebox.showinfo("Echo", response)

def create_group(group_name, user_socket):
    if group_name not in groups:
        groups[group_name] = []  # Initialize an empty list for the group members
        if user_socket:
            groups[group_name].append(user_socket)  # Add the first user to the new group
        return f"Group '{group_name}' created successfully."
    else:
        return f"Group '{group_name}' already exists."

def join_group(group_name, user_socket):
    if group_name in groups:
        if user_socket not in groups[group_name]:
            groups[group_name].append(user_socket)  # Add user to the group
            return f"Joined group '{group_name}' successfully."
        else:
            return f"You are already in the group '{group_name}'."
    else:
        return f"Group '{group_name}' does not exist."

def add_user_to_group(group_name, username):
    # Find the user's socket based on username
    for client_socket, user_name in active_users.items():
        if user_name == username:
            # Add the socket to the group if the group exists
            if group_name in groups:
                if client_socket not in groups[group_name]:
                    groups[group_name].append(client_socket)
                    return f"User '{username}' added to group '{group_name}' successfully."
                else:
                    return f"User '{username}' is already in the group '{group_name}'."
            else:
                return f"Group '{group_name}' does not exist."
    
    return f"User '{username}' is not connected."


        
def search_messages(search_entry, chat_display):
    search_term = search_entry.get()
    chat_display.tag_remove("highlight", "1.0", tk.END)
    
    if search_term:
        start_pos = "1.0"
        while True:
            start_pos = chat_display.search(search_term, start_pos, stopindex=tk.END)
            if not start_pos:
                break
            end_pos = f"{start_pos}+{len(search_term)}c"
            chat_display.tag_add("highlight", start_pos, end_pos)
            start_pos = end_pos
        chat_display.tag_config("highlight", background="yellow", foreground="black")

def add_user_to_group_prompt():
    group_name = create_custom_dialog("Add to Group", "Enter Group Name:")
    username = create_custom_dialog("Add to Group", "Enter Username to Add:")
    
    if group_name and username:
        # Call the function to add the user to the group
        response = add_user_to_group(group_name, username)
        messagebox.showinfo("Echo", response)


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 9999))
    server_socket.listen(5)

    root = tk.Tk()
    root.title("Echo - Server")
    root.state('zoomed')
    root.configure(bg="#2b2b2b")

    header = tk.Label(root, text="Server Chat", bg="#2b2b2b", fg="white", font=("Helvetica", 16, "bold"))
    header.pack(pady=10)

    main_frame = tk.Frame(root, bg="#2b2b2b")
    main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    group_frame = tk.Frame(root, bg="#2b2b2b")
    group_frame.pack(pady=5, padx=10, fill=tk.X)

    group_frame = tk.Frame(root, bg="#2b2b2b")
    group_frame.pack(pady=5, padx=10, fill=tk.X)

    chat_display = scrolledtext.ScrolledText(main_frame, state=tk.DISABLED, bg="#1e1e1e", fg="white", font=("Helvetica", 12))
    chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    user_list = Listbox(main_frame, bg="#1e1e1e", fg="white", font=("Helvetica", 12))
    user_list.pack(side=tk.RIGHT, fill=tk.Y)

    message_frame = tk.Frame(root, bg="#2b2b2b")
    message_frame.pack(pady=5, padx=10, fill=tk.X)

    message_entry = tk.Entry(message_frame, bg="#3c3c3c", fg="white", font=("Helvetica", 12))
    message_entry.pack(side=tk.LEFT, pady=5, padx=(0, 5), fill=tk.X, expand=True)

    send_button = tk.Button(message_frame, text="Send", bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"))
    send_button.pack(side=tk.RIGHT, pady=5)

    search_frame = tk.Frame(root, bg="#2b2b2b")
    search_frame.pack(pady=5)

    search_label = tk.Label(search_frame, text="Search Messages:", bg="#2b2b2b", fg="white", font=("Helvetica", 12))
    search_label.pack(side=tk.LEFT, padx=(5, 2))

    search_entry = tk.Entry(search_frame, bg="#3c3c3c", fg="white", font=("Helvetica", 12))
    search_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

    search_button = tk.Button(search_frame, text="Search", command=lambda: search_messages(search_entry, chat_display), bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"))
    search_button.pack(side=tk.LEFT, padx=(5, 5))
    client_queue = queue.Queue()

    create_group_button = tk.Button(
        group_frame,
        text="Create Group",
        bg="#4CAF50",
        fg="white",
        font=("Helvetica", 12, "bold"),
        command=lambda: create_group_prompt()
    )
    create_group_button.pack(side=tk.LEFT, padx=5)

    join_group_button = tk.Button(
        group_frame,
        text="Join Group",
        bg="#008CBA",
        fg="white",
        font=("Helvetica", 12, "bold"),
        command=lambda: join_group_prompt()
    )
    join_group_button.pack(side=tk.LEFT, padx=5)

    # New "Add to Group" Button
    add_to_group_button = tk.Button(
        group_frame,
        text="Add User to Group",
        bg="#FF9800",
        fg="white",
        font=("Helvetica", 12, "bold"),
        command=lambda: add_user_to_group_prompt()
    )
    add_to_group_button.pack(side=tk.LEFT, padx=5)


    def accept_connections():
        while True:
            client_socket, addr = server_socket.accept()
            client_queue.put(client_socket)

    def process_client():
        if not client_queue.empty():
            client_socket = client_queue.get()
            auth_window = tk.Toplevel(root)
            auth_window.title("User Authentication")
            auth_window.geometry("300x200")
            auth_window.configure(bg="#2b2b2b")
            
            header = tk.Label(auth_window, text="User Authentication", bg="#2b2b2b", fg="white", font=("Helvetica", 14, "bold"))
            header.pack(pady=10)

            def handle_login():
                username = create_custom_dialog("Login", "Enter Username:")
                password = create_custom_dialog("Login", "Enter Password:", is_password=True)
                if login_user(username, password):
                    messagebox.showinfo("Echo", "Login Successful!")
                    auth_window.destroy()
                    user_list.insert(tk.END, username)

                    # Add the user to active_users after successful login
                    active_users[client_socket] = username

                    # Start the client handler thread
                    threading.Thread(target=handle_client, args=(client_socket, chat_display, user_list, username)).start()
                    send_button.config(command=lambda: send_message(client_socket, message_entry, username, chat_display))
                else:
                    messagebox.showerror("Echo", "Login Failed!")

            def handle_register():
                username = create_custom_dialog("Register", "Enter Username:")
                password = create_custom_dialog("Register", "Enter Password:", is_password=True)
                if register_user(username, password):
                    messagebox.showinfo("Echo", "Registration Successful!")
                else:
                    messagebox.showerror("Echo", "Username already exists!")

            login_button = tk.Button(auth_window, text="Login", command=handle_login, bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"))
            login_button.pack(pady=10)

            register_button = tk.Button(auth_window, text="Register", command=handle_register, bg="#008CBA", fg="white", font=("Helvetica", 12, "bold"))
            register_button.pack(pady=10)

        root.after(100, process_client)

    threading.Thread(target=accept_connections, daemon=True).start()
    root.after(100, process_client)

    root.mainloop()
    server_socket.close()

if __name__ == "__main__":
    start_server()
