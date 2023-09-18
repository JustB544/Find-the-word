// Js for communicating with api and flask server

const options = {
    method: 'GET',
    url: 'https://wordsapiv1.p.rapidapi.com/words/',
    params: {},
    headers: {
      'X-RapidAPI-Key': auth_key,
      'X-RapidAPI-Host': 'wordsapiv1.p.rapidapi.com'
    }
  };

async function call_test(count, start){
    return await axios.get(`/test_words/${count}?start=${start}`)
}

