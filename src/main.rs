extern crate rustc_serialize as serialize;

use std::io::Read;
use std::fs::File;
use serialize::hex::{FromHex, ToHex};

// Not a library yet! Only for live testing
// Will soon become one and will have tests on it

// Hexing function
fn hexed(encode: &str) -> String {
    // only as a helper function
    encode.as_bytes().to_hex()
}

// Hex-decoding function
fn charred(decode: Vec<u8>) -> Vec<u8> {
    // Mostly, I try to stick to immutable borrows, but from_utf8() requires Vec<u8>
    let text = String::from_utf8(decode).unwrap();
    // unwrap the values from Ok(value)
    text.from_hex().unwrap()
}

// Gives a vector of file contents
fn fopen(path: &str) -> (usize, Vec<u8>) {
    let file = File::open(path);
    let mut contents: Vec<u8> = Vec::new();
    // of course, assuming that there won't be any problem in reading the file
    let file_size = file.unwrap().read_to_end(&mut contents).unwrap();
    (file_size, contents)
}

// Shifts the vector elements according to the given amount
fn shift(text: &Vec<u8>, amount: u8) -> Vec<u8> {
    let mut shifted_text = Vec::new();
    let mut shift_by: u8;
    for byte in text {
        // wrap around the boundary if the sum overflows
        shift_by = amount.wrapping_add(*byte);
        shifted_text.push(shift_by);
    } shifted_text
}

// Byte-wise XOR of vector elements according to a given string
fn xor(text: &Vec<u8>, key: &str) -> Vec<u8> {
    let mut xorred: Vec<u8> = Vec::new();
    let key_array = key.as_bytes();
    let (mut i, mut j) = (0, 0);
    while i < text.len() {
        xorred.push(text[i] ^ key_array[j]);
        i += 1; j += 1;
        if j == key.len() { j = 0; }
    } xorred
}

// Invokes the helper functions and does some useful stuff
fn zombify(mode: u8, data: &Vec<u8>, key: &str) -> Vec<u8> {
    let hexed_key = hexed(key);
    let mut amount: u8 = 0;
    for byte in hexed_key.as_bytes() {
        amount = amount.wrapping_add(*byte);
    } let mut text: Vec<u8> = data.clone();
    if mode == 1 {
        // encrypt the thing
        text = data.to_hex().into_bytes();
        let shifted_text = shift(&text, amount);
        xor(&shifted_text, &key)
    } else {
        let limit: u8 = 0;
        // shift by (256 - amount) for the reverse process
        amount = limit.wrapping_sub(amount);
        let shifted_text = xor(&text, &key);
        shift(&shifted_text, amount)
    }
}

// Checks if the big vector contains the small vector slice
fn search(text: &Vec<u8>, word: &str) -> u8 {
    let mut count: u8 = 0;
    let word_array = word.as_bytes();
    let length = text.len() - word.len() + 1;
    for i in 0..length {
        if text[i..text.len()].starts_with(&word_array) {
            count += 1;
        }
    } count
}

fn main() {

    // let text: Vec<u8> = vec![104, 101, 104, 101, 104, 101];
    // let put_in = zombify(1, &text, "pass123");
    // println!("{:?}", put_in);
    // let file_path = "/home/wafflespeanut/Desktop/stuff";
    // let put_in = fopen(file_path).1;
    // let got_back = charred(zombify(0, &put_in, "pass123"));
    // println!("{:?}", got_back);
    // println!("{:?}", search(&text, "he"));
    
}
