document.getElementById("subscribe-btn").addEventListener('click',()=>{
    let email = document.getElementById("subscribeEmail").value;
    if(email != ""){
        fetch(`/api/subscribe/${email}`,{
            method:"POST",
            cache:"no-cache"
        }).then((response)=>{
            response.text().then((msg)=>{
                if(msg == "added"){
                    window.location.href=`./subscribe/welcome/${email}`;
                }else if(msg == "return"){
                    window.location.href=`./subscribe/return/${email}`;
                }else{
                    window.location.href="./home";
                }
            })
            
        })
    }
})