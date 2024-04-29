function deleteFromCart(element){
    category = element.getAttribute('data-category');
    id = element.getAttribute('data-id');
    fetch(`/api/delete/item/cart/${id}/${category}`,{
        method:"POST",
        cache:"no-cache"
    }).then(()=>{
        window.location.reload();
    })
}

window.onload = function(){
    let cart_quant_ref = document.getElementById("cart-number");
    fetch(`/api/check/cart/quantity`,{
        method:"GET",
        cache:"no-cache"
    }).then((response)=>{
        response.text().then((quantity)=>{
            cart_quant_ref.innerHTML = quantity;
            loading_screen_off();
        })
    })
}

function loading_screen_on(){
    document.getElementById("loading-screen").className = "loading-screen-active";
}

function loading_screen_off(){
    document.getElementById("loading-screen").className = "loading-screen";
}

function submitForm(name){
    document.getElementById("sup-data").value = String(name);
    var form = document.getElementById("category-footer-form");
    form.submit();
}

function addToFav(element){
    loading_screen_on();
    category = element.getAttribute('data-category');
    id = element.getAttribute('data-id');
    fetch(`/api/add/item/fav/${id}/${category}`,{
        method:"POST",
        cache:"no-cache"
    }).then(()=>{
        ref = document.getElementById(`${id}-heart-btn-holder`);
        ref.innerHTML = `<div class="btn btn-success text-white" onclick="removeFromFav(this)"
        data-category="${category}" data-id="${id}"><i class="fas fa-heart"></i></div>`;
        loading_screen_off();
    })
}

function removeFromFav(element){
    loading_screen_on();
    category = element.getAttribute('data-category');
    id = element.getAttribute('data-id');
    fetch(`/api/delete/item/fav/${id}/${category}`,{
        method:"POST",
        cache:"no-cache"
    }).then(()=>{
        ref = document.getElementById(`${id}-heart-btn-holder`);
        ref.innerHTML = `<div class="btn btn-success text-white" onclick="addToFav(this)"
        data-category="${category}" data-id="${id}"><i class="far fa-heart"></i></div>`;
        loading_screen_off();
    })
}