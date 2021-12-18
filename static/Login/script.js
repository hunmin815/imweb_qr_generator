// JQUERY
$(function() {
	
	// var images = ['https://wallpapersite.com/images/pages/pic_w/1063.jpg', 'http://www.hdwallpaper.nu/wp-content/uploads/2017/04/PLAYERUNKNOWNS-BATTLEGROUNDS-12937710.jpg', 'https://www.hdwallpapers.in/walls/overwatch_4k-HD.jpg', 'https://images.alphacoders.com/186/186993.jpg', 'https://images4.alphacoders.com/602/thumb-1920-602788.png'];
  var images = ['./static/Login/wallpaper4.png'];
   $('#container').append('<style>#container, .acceptContainer:before, #logoContainer:before {background: url(' + images[Math.floor(Math.random() * images.length)] + ') center fixed }');
	
	
	
	
	setTimeout(function() {
		$('.logoContainer').transition({scale: 1}, 550, 'ease');
		setTimeout(function() {
			$('.logoContainer .logo').addClass('loadIn');
			setTimeout(function() {
				$('.logoContainer .text').addClass('loadIn');
				setTimeout(function() {
					$('.acceptContainer').transition({height: '431.5px'});
					setTimeout(function() {
						$('.acceptContainer').addClass('loadIn');
						setTimeout(function() {
							$('.formDiv, form h1').addClass('loadIn');
						}, 1)   // 로그인 입력 텍스트 박스
					}, 400)   // 로그인 입력 박스 배경
				}, 120)     // 로그인 입력 박스 높이
			}, 100)
		}, 15)          // 로고 이미지
	}, 15)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
});