import network
import socket
import utime
import machine

led = machine.Pin('LED', machine.Pin.OUT)

def access_point():
    ap = network.WLAN(network.AP_IF) # Create access-point interface
    ap.config(essid='UDO-W', password='12345678') # Set the SSID and PASSWORD of the access point
    ap.active(True) # Activate the interface

    ip = ap.ifconfig()[0] # Get the IP address
    print(f'ip = {ip}')
    
    return ip
    
def get_file(file_name):
    #Template HTML
    with open(file_name, 'r') as file:
        html = file.read()        
    
    return html


def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(3)
    return connection

def get_message(request, position_msg):
    # se omite el 'message='
    position = position_msg+8
    message = request[position::]
    # los + se resplazan por espacios
    message = message.replace('+', ' ')
    # si hay algun simbolo codificado
    posi = message.find('%')
    
    # pasa por los filtros para remplazarlos
    if posi!=-1:
        # vocales
        if message.find('%C3%A1') != -1: message = message.replace('%C3%A1','á')
            
        if message.find('%C3%A9') != -1: message = message.replace('%C3%A9','é')
            
        if message.find('%C3%AD') != -1: message = message.replace('%C3%AD','í')
            
        if message.find('%C3%B3') != -1: message = message.replace('%C3%B3','ó')
            
        if message.find('%C3%BA') != -1: message = message.replace('%C3%BA','ú')
        
        # ñ
        if message.find('%C3%B1') != -1: message = message.replace('%C3%B1','ñ')
            
        # simbolos
        if message.find('%3F') != -1: message = message.replace('%3F','?')
            
        if message.find('%C2%BF') != -1: message = message.replace('%C2%BF','¿')
        
        if message.find('%2C') != -1: message = message.replace('%2C',',')
    
    # retorna sin el ultimo caracter (comilla final)
    return message[:-1]


def get_user(request, position_user):

    data = request[position_user::]
    data = data[:-1]
    print(data)

    array = data.split('&')

    data_user = []

    for value in array:
        val = value.split('=')
        # se apila el valor en mayuscula
        data_user.append(val[1].upper())

    return data_user


def login(file, user, password):
    with open(file, 'r') as f:
        for line in f:
            user_file, password_file = line.strip().split(';')
            if user_file == user and password_file == password:
                return True
    return False


def get_session(file, ip):
    with open(file, 'r') as f:
        for line in f:
            ip_file, user = line.strip().split(';')
            print(user)
            if ip_file == ip:
                return user
    return False


def server(s):
    # Delete all sessions
    with open('sessions.csv', 'w') as file:
        pass
        
    while True:
        try:
            # Accept incoming connection
            conn, addr = s.accept()
            print('Client connected from', addr)
            
            # Receive request with a limit of 1024 bytes
            r = conn.recv(1024)
            
            request = str(r)
        
            print('request: ', request)
        
            #user_ip = addr[0]
        
            position_msg = request.find('message=')
            
            if position_msg != -1:
                message = get_message(request, position_msg)
            
            log = False
            position_user = request.find('user=')
            
            if position_user != -1:
                data_user = get_user(request, position_user)
                print(data_user)
                
                if data_user[0] != '' and data_user[1] != '':
                    log = login('users.csv', data_user[0], data_user[1])
                    
                    if log:
                        print('El usuario y la contraseña coinciden')
                        user_ip = addr[0]
                        name_user = data_user[0]
                        
                        session = get_session('sessions.csv', user_ip)
                        
                        if not session:
                            with open('sessions.csv', 'a') as file:
                                table = file.write(f"{ user_ip };{ name_user }\n")
                            
                    else:
                        print('El usuario y la contraseña no coinciden')
            
        
            try:
                request = request.split()[1]
            except IndexError:
                pass
            
            html = ''
            
            if request == '/':
                # se obtiene el body del login
                body = get_file('login_body.html')
                # se une el head y el body
                html = get_file('head.html') + body
                
            elif request == '/chat?':
                
                ip_user = addr[0]
                user_name = get_session('sessions.csv', ip_user)
                
                if user_name:
                    #se le agrega la parte dinamica al body
                    body = get_file('chat_body.html') % get_file('table_body.html')
                    #se une el head con el body
                    html = get_file('head.html') + body
                else:
                    # se obtiene el body del login
                    body = get_file('login_body.html')
                    # se une el head y el body
                    html = get_file('head.html') + body
        
            elif request == '/clear?':
                # Clear table body
                with open('table_body.html', 'w') as file:
                    pass
                #se le agrega la parte dinamica al body
                body = get_file('chat_body.html') % get_file('table_body.html')
                #se une el head con el body
                html = get_file('head.html') + body
            
            elif request == '/send?':
                current_time = utime.localtime()
                hora = "{:02d}:{:02d}:{:02d}".format(current_time[3],current_time[4],current_time[5])
                fecha = "{:02d}/{:02d}/{:02d}".format(current_time[2],current_time[1],current_time[0])
                
                ip_user = addr[0]
                user_name = get_session('sessions.csv', ip_user)
                
                # Create new message
                new_message = f"""<tr>
                                    <td>{ user_name }</td>
                                    <td>{ message }</td>
                                    <td>{ hora }</td>
                                    <td>{ fecha }</td>
                                    </tr>
                                """
                # Add to table_body
                with open('table_body.html', 'a') as file:
                    table = file.write(new_message)
                    
                #se le agrega la parte dinamica al body
                body = get_file('chat_body.html') % get_file('table_body.html')
                #se une el head con el body
                html = get_file('head.html') + body
            
            
            conn.sendall(html)
            conn.close()
        
        except OSError as e:
            conn.close()
            print('connection closed')
            
        
try:
    ip = access_point()
    s = open_socket(ip)
    server(s)
    
except KeyboardInterrupt:
    machine.reset()
