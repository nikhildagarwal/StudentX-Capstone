var prev_selected = null;

function triggerFilter(){
    let value = document.getElementById("filter-selection").value;
    if(prev_selected == null){
        index = document.getElementById("filter-selection").selectedIndex;
        prev_selected = document.getElementById("filter-selection").options[index].value;
        return;
    }
    if(value != prev_selected){
        submitSortForm(value);
    }
}

var listing_area_ref = document.getElementById("listing-title");


function addToCart(element){
    category = element.getAttribute('data-category');
    id = element.getAttribute('data-id');
    fetch(`/api/add/item/cart/${id}/${category}`,{
        method:"POST",
        cache:"no-cache"
    }).then(()=>{
        window.location.href="./cart";
    })
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
        ref.innerHTML = `<div class="btn btn-success text-white" onclick="addToFave(this)"
        data-category="${category}" data-id="${id}"><i class="far fa-heart"></i></div>`;
        loading_screen_off();
    })
}

function loading_screen_on(){
    document.getElementById("loading-screen").className = "loading-screen-active";
}

function loading_screen_off(){
    document.getElementById("loading-screen").className = "loading-screen";
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

function submitSearchForm(element){
    var form = document.getElementById("shop-search-form");
    let sentence = element.innerHTML;
    document.getElementById("inputModalSearch").value = sentence;
    form.submit();
}

function submitSortForm(value){
    var form = document.getElementById("shop-sort-form");
    document.getElementById("sort-input").value=value;
    loading_screen_on();
    form.submit()
}

function topage(element){
    var form = document.getElementById("page_form");
    let page = Number(element.innerHTML);
    let current_page = Number(form.getAttribute("data-current-page"));
    if (current_page == page){
        return;
    }
    document.getElementById("page_number_input").value = page;
    form.submit();
}

