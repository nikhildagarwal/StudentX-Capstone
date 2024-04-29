var socketio = io();

const date_array = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const hour_array = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
var uid_to_name = null;
var chat_id_to_uid = null;
var current_active_chat = null;
var current_active_chat_ref = null;
var messages_ref = document.getElementById("message-box");
var messages_header_ref = document.getElementById("message-header");
var MY_ID = null;

var lock_setting_tracker = "off";
var time_setting_tracker = "off";

var order_tracker = [];
var time_tracker = new Map();

function generate_time_string_from_timestamp(timestamp){
    timestamp *= 1000;
    let date = new Date(timestamp);
    let today = new Date();
    today.setHours(0, 0, 0, 0);
    let yesterday = new Date(today.getTime() - (24 * 60 * 60 * 1000));
    return generate_time_string(date, today, yesterday);
}

function set_chat_list(ot){
    chat_list_ref.innerHTML = `<h3><i class="fa-regular fa-message" id="header-icon"></i> Chats</h3>`;
    let length = ot.length;
    for(let i = 0; i<length; i++){
        chat_list_ref.innerHTML += ot[i][1];
    }
    chat_buttons = document.querySelectorAll(".chat");
    chat_buttons.forEach((item)=>{
        chat_list_button_creator(item);
    })
}


function update_order_trackers(new_message, new_timestamp, chat_id, read){
    fetch(`/api/chat/update/read/${localStorage.getItem('my-uid')}/${read}/${chat_id}`,{
        method:"POST",
        cache:"no-cache"
    }).then(()=>{
        let time_string_new = generate_time_string_from_timestamp(new_timestamp);
        let curr = time_tracker.get(chat_id);
        let value = chat_id_to_uid.get(chat_id);
        curr[0] = new_timestamp;
        curr[2] = new_message;
        let bc = read == true ? 'recent-msg' : 'recent-msg-bold';
        /**Make the message bold if read is FALSE */
        curr[1] = `<div class="chat" 
        data-chat-id="${chat_id}" data-my-uid="${localStorage.getItem('my-uid')}" 
        data-other-uid="${value}">
                ${uid_to_name.get(value)}
                <div class="${bc}">
                    ${new_message}
                    <div class="recent-msg-time">
                        ${time_string_new}
                    </div>
                </div>
            </div>`;
        order_tracker.sort((a,b)=>b[0]-a[0]);
        set_chat_list(order_tracker);
    });
}

window.onload = function(){
    fetch(`/chat/fetch/dictionaries`,{
        method:"GET",
        cache:"no-cache"
    }).then((response)=>{
        response.json().then((result)=>{
            if(!result.no_chats){
                uid_to_name = new Map(Object.entries(result.uid_to_name));
                chat_id_to_uid = new Map(Object.entries(result.chat_id_to_uid));
                chat_id_to_timestamp = new Map(Object.entries(result.recent));
                chat_list_ref = document.getElementById("chat_list");
                chat_id_to_uid.forEach((value, key) => {
                    let timestamper = chat_id_to_timestamp.get(key).timestamp;
                    let recent_msg = chat_id_to_timestamp.get(key).message;
                    let read_value = chat_id_to_timestamp.get(key).read;
                    console.log(recent_msg + " : " + read_value);
                    let time_string = generate_time_string_from_timestamp(timestamper);
                    if(recent_msg == undefined){
                        recent_msg = "start a conversation";
                        time_string = "";
                        read_value = true
                    }
                    let bold_class = read_value == true ? 'recent-msg' : 'recent-msg-bold';
                    array_object = [timestamper, `<div class="chat" 
                    data-chat-id="${key}" data-my-uid="${result.my_uid}" 
                    data-other-uid="${value}">
                            ${uid_to_name.get(value)}
                            <div class="${bold_class}">
                                ${recent_msg}
                                <div class="recent-msg-time">
                                    ${time_string}
                                </div>
                            </div>
                        </div>`, recent_msg];
                    order_tracker.push(array_object);
                    time_tracker.set(key, array_object);
                });
                order_tracker.sort((a,b)=>b[0]-a[0]);
                set_chat_list(order_tracker);
                load_chat_preferences();
                /**
                 * LOADING SCREEN OFF
                 */
                document.getElementById("loading-screen").className = "loading-screen";
            }else{
                console.log("no chats found");
            }
        })
    })
}

var time_of_last_message_seconds = null;

function chat_list_button_creator(item){
    item.addEventListener('click',()=>{
        time_of_last_message_seconds = null;
        let chat_id = item.getAttribute('data-chat-id');
        let my_id = item.getAttribute('data-my-uid');
        MY_ID = my_id
        let other_id = item.getAttribute('data-other-uid');
        localStorage.setItem('my-uid', my_id);
        localStorage.setItem('chat-uid', chat_id);
        localStorage.setItem('other-uid', other_id);
        messages_header_ref.innerHTML = "";
        messages_ref.innerHTML = "";
        fill_right_hand_side(chat_id, other_id);
        current_active_chat = chat_id;
    })
}

var nma_ref = document.getElementById("nma");

function fill_right_hand_side(chat_id, other_id){
    messages_header_ref.innerHTML = `<h3>${uid_to_name.get(other_id)}</h3>`;
    document.getElementById("loading-screen").className = "loading-screen-active";
    fetch(`/api/get/messages/${chat_id}`,{
        method: "GET",
        cache: "no-cache"
    }).then((response)=>{
        response.json().then((result)=>{
            let counter1 = 0;
            try{
                result.messages.map((item)=>{
                    if(counter1 == 0){
                        counter1++;
                        document.getElementById("message-box").className = "message";
                        document.getElementById("nma").className = "no-display";
                    }
                    createMessage(item.uid, item.message, item.timestamp, chat_id);
                });
            }catch (error){}
            let counter2 = 0;
            try{
                
                result.new_messages.map((item)=>{
                    if(counter2 == 0){
                        counter2++;
                        document.getElementById("message-box").className = "message";
                        document.getElementById("nma").className = "no-display";
                    }
                    createMessage(item.uid, item.message, item.timestamp,chat_id);
                });
            }catch (error){}
            if(counter1 == 0 && counter2 == 0){
                document.getElementById("message-box").className = "no-display";
                document.getElementById("nma").className = "no-messages-available";
            }
            document.getElementById("message-header").className = "head";
            document.getElementById("message-view-area").className = "message-area";
            document.getElementById("message-input-area").className = "message-input-container";
            document.getElementById("ncs").className = "no-display";
            document.getElementById("ncst").className = "no-display";
            document.getElementById("ncsst").className = "no-display";
            var message_scroll = document.getElementById("message-box");
            message_scroll.scrollTop = message_scroll.scrollHeight;
            message_scroll.scrollIntoView(false);
            document.getElementById("loading-screen").className = "loading-screen";
        })
    });
}

function generate_time_string(date, today, yesterday){
    const day = date.getDay();
    const month = date_array[Number(date.getMonth())];
    const hour = hour_array[Number(date.getHours())];
    var minutes = date.getMinutes();
    if(minutes < 10){
        minutes = String(minutes);
        minutes = "0" + minutes;
    }
    var time_suffix = "PM";
    if(Number(date.getHours()) < 12){
        time_suffix = "AM";
    }
    let isToday = date.getMonth() == today.getMonth() && date.getDate() == today.getDate() && date.getFullYear() == today.getFullYear();
    let isYesterday = null;
    if(isToday){
        isYesterday = false;
    }else{
        isYesterday = date.getMonth() == yesterday.getMonth() && date.getDate() == yesterday.getDate() && date.getFullYear() == yesterday.getFullYear();
    }
    if(isToday){
        return `Today at ${hour}:${minutes} ${time_suffix}`;
    }else if(isYesterday){
        return `Yesterday at ${hour}:${minutes} ${time_suffix}`;
    }else{
        return `${days[day]}, ${month} ${date.getDate()} at ${hour}:${minutes} ${time_suffix}`;
    }
}

const createMessage = (uid, msg, timestamp, chat_id) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today.getTime() - (24 * 60 * 60 * 1000));
    if(nma_ref.className != "no-display"){
        nma_ref.className = "no-display";
        document.getElementById("message-box").className = "message";
    }
    const date = new Date(timestamp * 1000);
    let content = "";
    let output = generate_time_string(date, today, yesterday);
    let day = date.getDay();
    let month = date_array[Number(date.getMonth())];
    let hour = hour_array[Number(date.getHours())];
    let minutes = date.getMinutes();
    if(minutes < 10){
        minutes = String(minutes);
        minutes = "0" + minutes;
    }
    let time_suffix = "PM";
    if(Number(date.getHours()) < 12){
        time_suffix = "AM";
    }
    var date_right_class = "date-right-off";
    var date_left_class = "date-left-off";
    if(time_setting_tracker == "on"){
        date_right_class = "date-right";
        date_left_class = "date-left";
    }
    var hide_right_class = "hide-right-off";
    var hide_left_class = "hide-left-off";
    var text_right_class = "text-right";
    var text_left_class = "text-left";
    if(lock_setting_tracker == "on"){
        hide_right_class = "hide-right";
        hide_left_class = "hide-left";
        text_right_class = "text-right-off";
        text_left_class = "text-left-off";
    }
    
    let length = msg.length;
    var hide_word = "";
    for(let i = 0; i<length-1; i++){
        hide_word += "* ";
    }
    hide_word += "*";
    if(time_of_last_message_seconds == null){
        content += `
        <div class="item-center-skinny">
            ${output}
        </div>
        `;
    }else if((timestamp - time_of_last_message_seconds) < 3600 && (timestamp - time_of_last_message_seconds) >= 60){
        content += `
        <div class="item-center-skinny">
            &nbsp;
        </div>
        `;
    }else if((timestamp - time_of_last_message_seconds) >= 3600){
        content += `
        <div class="item-center-skinny">
            ${output}
        </div>
        `;
    }
    time_of_last_message_seconds = timestamp;
    if(uid == localStorage.getItem("my-uid")){
        content += `
            <div class="item-right">
                <div class="${text_right_class}">${msg}</div>
                <div class="${hide_right_class}">${hide_word}</div>
                <div class="${date_right_class}">${month} ${date.getDate()}, ${date.getFullYear()} &nbsp;${hour}:${minutes} ${time_suffix}</div>
            </div>
            `;
    }else{
        content += `
            <div class="item-left">
                <div class="${text_left_class}">${msg}</div>
                <div class="${hide_left_class}">${hide_word}</div>
                <div class="${date_left_class}">${month} ${date.getDate()}, ${date.getFullYear()} &nbsp;${hour}:${minutes} ${time_suffix}</div>
            </div>
            `;
    }
    update_order_trackers(msg, timestamp, chat_id, true);
    //<div class="meta-info">${timestamp}</div>
    messages_ref.innerHTML += content;
};

window.onbeforeunload = function(){
    update_chat_preferences();
}



socketio.on("message", (data)=>{
    curr_uid = localStorage.getItem('my-uid')
    if(data.chat_id == current_active_chat){
        createMessage(data.uid, data.message, data.timestamp, data.chat_id);
    }else{
        update_order_trackers(data.message, data.timestamp, data.chat_id, false);
    }
});

document.getElementById("send-btn").addEventListener('click',()=>{
    let message = document.getElementById("message-input");
    if(message.value == ""){
        return;
    }
    socketio.emit("message", {'data':message.value, 
                            'chat_id':current_active_chat, 
                            'sender_id': localStorage.getItem('my-uid')});
    message.value = "";
})

var lock_ref = document.getElementById("lock-setting");
var lock_check_ref = document.getElementById("lock-setting-check");

function turn_lock_on(){
    lock_ref.className = "fa-solid fa-lock on";
        lock_setting_tracker = "on";
        lock_check_ref.className = "fa-solid fa-square-check";
        try{
            document.querySelectorAll(".hide-left-off").forEach((button)=>{
                button.className = "hide-left";
            })
        }catch{console.log("error");}
        try{
            document.querySelectorAll(".hide-right-off").forEach((button)=>{
                button.className = "hide-right";
            })
        }catch{console.log("error");}
        try{
            document.querySelectorAll(".text-left").forEach((button)=>{
                button.className = "text-left-off";
            })
        }catch{console.log("error");}
        try{
            document.querySelectorAll(".text-right").forEach((button)=>{
                button.className = "text-right-off";
            })
        }catch{console.log("error");}
}

function turn_lock_off(){
    lock_ref.className = "fa-solid fa-lock";
        lock_setting_tracker = "off";
        lock_check_ref.className = "fa-regular fa-square-check";
        try{
            document.querySelectorAll(".hide-left").forEach((button)=>{
                button.className = "hide-left-off";
            })
        }catch{console.log("error");}
        try{
            document.querySelectorAll(".hide-right").forEach((button)=>{
                button.className = "hide-right-off";
            })
        }catch{console.log("error");}
        try{
            document.querySelectorAll(".text-left-off").forEach((button)=>{
                button.className = "text-left";
            })
        }catch{console.log("error");}
        try{
            document.querySelectorAll(".text-right-off").forEach((button)=>{
                button.className = "text-right";
            })
        }catch{console.log("error");}
}

lock_ref.addEventListener('click',()=>{
    if(lock_setting_tracker == "off"){
        turn_lock_on();
    }else{
        turn_lock_off();
    }
})



var time_setting_check = document.getElementById("time-setting-check");
var time_setting_ref = document.getElementById("time-setting");

function turn_time_on(){
    time_setting_ref.className = "fa-solid fa-hourglass-start on";
        time_setting_tracker = "on";
        time_setting_check.className = "fa-solid fa-square-check";
        try{
            document.querySelectorAll(".date-left-off").forEach((button)=>{
                button.className = "date-left";
            })
        }catch{console.log("error");}
        try{
            document.querySelectorAll(".date-right-off").forEach((button)=>{
                button.className = "date-right";
            })
        }catch{console.log("error");}
}

function turn_time_off(){
    time_setting_check.className = "fa-regular fa-square-check";
    time_setting_ref.className = "fa-solid fa-hourglass-start";
    time_setting_tracker = "off";
    try{
        document.querySelectorAll(".date-left").forEach((button)=>{
            button.className = "date-left-off";
        })
    }catch{console.log("error");}
    try{
        document.querySelectorAll(".date-right").forEach((button)=>{
            button.className = "date-right-off";
        })
    }catch{console.log("error");}
}

time_setting_ref.addEventListener('click',()=>{
    if(time_setting_ref.className == "fa-solid fa-hourglass-start"){
        turn_time_on();
    }else{
        turn_time_off();
    }
})

var settings_tracker = "off";
var setting_header = document.getElementById("setting-header");
var settings_list = document.getElementById("settings-list");
var setting = document.getElementById("settings");
var gear_ref = document.getElementById("header-icon-setting");

setting_header.addEventListener('click',()=>{
    
    if(settings_tracker == "on"){
        /*IF SETTINGS ON*/
        document.querySelectorAll(".setting-item").forEach((button)=>{
            button.className = "setting-item-off";
        });
        settings_tracker = "off";
        gear_ref.className = "fa-solid fa-gear off";
        setting.className = "fa-solid fa-caret-right";
        settings_list.style.width = "2.25%";
    }else{
        /*IF SETTINGS OFF*/
        settings_list.style.width = "24%";
        setting.className = "fa-solid fa-caret-left";
        setTimeout(function() {
            document.querySelectorAll(".setting-item-off").forEach((button)=>{
                button.className = "setting-item";
            });
            settings_tracker = "on";
            gear_ref.className = "fa-solid fa-gear";
        }, 250);
        
    }
})

function update_chat_preferences(){
    let key1 = lock_setting_tracker == "off" ? 0 : 1;
    let key2 = time_setting_tracker == "off" ? 0 : 1;
    fetch(`/api/chat/update/settings/${key1}/${key2}`,{
        method:"GET",
        cache:"no-cache"
    }).then(()=>{
        console.log("done")
    })
}

function load_chat_preferences(){
    fetch(`/api/chat/get/settings`,{
        method:"GET",
        cache:"no-cache"
    }).then((response)=>{
        response.json().then((result)=>{
            if(result.lock_setting == 1){
                turn_lock_on();
            }
            if(result.time_setting == 1){
                turn_time_on();
            }
        })
    })
}

function toggleSidebar() {
    var sidebar = document.getElementById("sidebar");
    if (sidebar.style.width === "15%") {
        sidebar.style.width = "0";
    } else {
        sidebar.style.width = "15%";
    }
}