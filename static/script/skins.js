window.dm_skin = "1";
window.tdm_skin = "73";

function changeSkinIndicators() {
    let paddedDM = `${dm_skin}`.padStart(4, "0");
    let paddedTDM = `${tdm_skin}`.padStart(4, "0");

    let dm = document.getElementById("dm_skin_indicator");
    let tdm = document.getElementById("tdm_skin_indicator");
    
    dm.src = `static/img/register/${paddedDM}.png`
    tdm.src = `static/img/register/${paddedTDM}.png`
}

function setSkin(skin) {
    dm_skin = skin;
    changeSkinIndicators();
}

function setTdmSkin(skin) {
    tdm_skin = skin;
    changeSkinIndicators();
}

async function addSkins() {
    let skinElement = document.getElementById("form_dm_skins");
    let tdmSkinElement = document.getElementById("form_tdm_skins");

    const skins = [1,2,3,4,6,7,8,9,11,12,13,14,15,16,17,18,19,21,22,23,24,25,26,
        27,28,29,31,32,33,34,35,36,37,41,42,43,44,45,46,47,48,49,61,
        69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,
        90,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,
        145,146,147,148,149,150];
    for(let skin of skins) {
        let padded = `${skin}`.padStart(4, "0");

        let item = document.createElement("a");
        let image = document.createElement("img");
        image.src = `static/img/register/${padded}.png`
        item.appendChild(image);
        item.setAttribute("class", "skin_item");
        item.setAttribute("onclick", `setSkin(${skin})`)
        //item.setAttribute("href", "#");

        skinElement.appendChild(item);
    }
    const tdmSkins = [73, 75, 77, 79, 81, 83, 85, 87, 89];
    for (let blueSkin of tdmSkins) {
        let item = document.createElement("a");

        let img1 = document.createElement("img");
        let padded1 = `${blueSkin}`.padStart(4, "0");
        img1.src = `static/img/register/${padded1}.png`;

        let img2 = document.createElement("img");
        let padded2 = `${blueSkin+1}`.padStart(4, "0");
        img2.src = `static/img/register/${padded2}.png`;
    
        item.appendChild(img1);
        item.appendChild(img2);

        //item.setAttribute("href", "#");
        item.setAttribute("onclick", `setTdmSkin(${blueSkin})`);
        item.setAttribute("class", "skin2_item");

        tdmSkinElement.appendChild(item);
    }
}

addSkins();
changeSkinIndicators();