function imgOut=readseq( readerobj,framenum )
%READSEQ Summary of this function goes here
%   Detailed explanation goes here

fid = fopen(readerobj.Path,'r','b');
endianType = 'ieee-le';
    bitstr = '';
    
    % PREALLOCATION
    imSize = [readerobj.Width,readerobj.Height];
    imgOut = zeros(imSize(2),imSize(1));
    switch readerobj.ImageBitDepthReal
        case 8
            bitstr = 'uint8';
        case {12,14,16}
            bitstr = 'uint16';
    end
    if isempty(bitstr)
        error('Unsupported bit depth');
    end
    
    nread = framenum-1;
    
        fseek(fid, 1024 + nread * readerobj.TrueImageSize, 'bof');
        tmp = fread(fid, readerobj.Width * readerobj.Height, bitstr, endianType);
        % max(tmp(:))

        imgOut(:,:) = permute(reshape(tmp,imSize(1),imSize(2),[]),[2,1,3]);
        tmp = fread(fid, 1, 'int32', endianType);
        tmp2 = fread(fid,2,'uint16', endianType);
        tmp = tmp/86400 + datenum(1970,1,1);
        readerobj.timestamp{nread + 1} = [datestr(tmp) ':' num2str(tmp2(1)),num2str(tmp2(2))];
        %readerobj.timestamp{nread + 1}


      
    
    

fclose(fid);


