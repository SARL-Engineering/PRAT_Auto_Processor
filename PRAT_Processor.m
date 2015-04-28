% --- Executes on button press in BATCHCALCU.
function varargout = PRAT_Processor(processing_path, output_path)

%%%%%%%%%% Decleration of variables %%%%%%%%%%
handles.batch_processing_path = processing_path;
handles.file_list=dir([handles.batch_processing_path, '\', '*.seq']);%get seq file list linux path
[handles.file_number, ~] = size(handles.file_list);

handles.save_path = output_path;

load([cd, '\settings.mat']);
handles.x1 = x1;  
handles.y1 = y1;
handles.r = r;
handles.x12 = x12;
handles.y12 = y12;
handles.x96 = x96;
handles.y96 = y96;

%%%%%%%%%% BEGINNING OF COPIED FUNCTION %%%%%%%%%%
x85=handles.x96-handles.x12+handles.x1;
y85=handles.y1-handles.y12+handles.y96;
handles.x85 = x85;         %
handles.y85 = y85;         %
%%%%%%%%%%%%caculate difference step of x in the same column
x_radius = zeros(8,12);
step_x_y_12 = (handles.x96 - handles.x12)/7;  %negtive or positive
step_x_y_1 = (handles.x85 - handles.x1)/7;    %negtive or positive

%%%%%%%%%%%%caculate x in the first and 12th columns
if step_x_y_12 == 0
    x_radius(:,12) = handles.x12;
else
    x_radius(:,12) = handles.x12:step_x_y_12:handles.x96; %12th colon value for x
end

if step_x_y_1 == 0 
    x_radius(:,1) = handles.x1;
else
    x_radius(:,1) = handles.x1:step_x_y_1:handles.x85;%first colon value for x
end 

%%%%%%%%%%%%%%caculate all coordinates for x %%%%%%%%%%%% 
for i = 1: 8 
    for j=1:12
        x_radius(i,j)= x_radius(i,1)+(j-1)*(x_radius(i,12)-x_radius(i,1))/11;
    end 
end 

y_radius = zeros(8,12);
step_y_y_1 = (handles.y12 - handles.y1)/11;  %negtive or positive
step_y_y_12 = (handles.y96 - handles.y85)/11;    %negtive or positive

%%%%%%%%%%%%caculate y in the first and 8th ranks
if step_y_y_12 == 0
   y_radius(8,:) = handles.y96;
else
    y_radius(8,:) = handles.y85:step_y_y_12:handles.y96; %12th colon value for y
end

if step_y_y_1 == 0
  y_radius(1,:) = handles.y1;
else 
    y_radius(1,:) = handles.y1:step_y_y_1:handles.y12;%first colon value for y
end

%%%%%%%%%%%%%%caculate all y 
for j=1:12
    for i = 1: 8 
         y_radius(i,j)=y_radius(1,j) + (i-1)*(y_radius(8,j)-y_radius(1,j))/7;
    end
end 


handles.x_radius = round(x_radius);%all value should be integer
handles.y_radius = round(y_radius);
%%%%%%%%%% END OF COPIED FUNCTION %%%%%%%%%%


for k=1:handles.file_number
    %set current time as MAT's name
    current_time = fix(clock);
    current_time_string_for_text_1 = [num2str(current_time(1)) '-' num2str(current_time(2)) '-' num2str(current_time(3))  ' '  num2str(current_time(4))  ':' num2str(current_time(5)) ':'  num2str(current_time(6))]; 
                   
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  


%     waitbar(i /(handles.file_number))    %process bar
    %vedio path for the 'i'th vedio
    vediopath =[handles.batch_processing_path, '\', handles.file_list(k).name];
    %%%%%%load seq vedio%%%%%%%%%%
    handles.readerobj=Norpix2MATLAB(vediopath);
    %number of frames 
    handles.nFrames = handles.readerobj.NumberOfFrames;
    %duaration time for vedio 
    handles.duration_time = handles.readerobj.Duration;


    %%%%save the n-th frame(displayed in plot) for all batch processing seq videos
    %readseq frame from seq file //
    
    %file name without extentions
    [~, name, ~] = fileparts(handles.file_list(k).name);
    handles.filename = name;
    %set current time as MAT's name
    current_time=fix(clock);
    current_time_string=[num2str(current_time(1)) '-' num2str(current_time(2)) '-' num2str(current_time(3))  '-'  num2str(current_time(4))  '-' num2str(current_time(5)) '-'  num2str(current_time(6))];

    %mirror the matrix in central colomn
     xx = handles.x_radius;
     yy = handles.y_radius;
    for m=1:8
        for n=1:6
            temp_x=xx(m,n);
            xx(m,n)=xx(m,12-n+1);
            xx(m,12-n+1)=temp_x;
            temp_y=yy(m,n);
            yy(m,n)=yy(m,12-n+1);
            yy(m,12-n+1)=temp_y;
        end
    end

    %matrix to vector
    x_vector= reshape(xx',1,[]);
    y_vector= reshape(yy',1,[]); 

    %%%%%%%initiate variables for each cycle%%%%%%
    frame_column = [];
    time_stamp   = [];
    time_stamp_temp = [];
    result_output_s=[];
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    %calculation 
%    result_s = differential_batch(x_vector,y_vector,handles.r,10,handles.readerobj);



%%%%%%%%%% this block substitute batch processing function, so it is convenient to add 'stop' function%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        % function output = differential_batch( centrex,centrey,radius,thres,readerobj )
        %copy input values.
        centrex = x_vector;   
        centrey = y_vector;
        radius=round(handles.r);%radius=handles.r;
        thres=10;
        readerobj=handles.readerobj;

    %%%%%%%%%%%
    framenum=readerobj.NumberOfFrames;
    result_s=zeros(framenum-1,96);
    for i=1:framenum-1

                 %pause here because running seq videos results in having no time 
                 %to respond to 'cancel' button and therefor cannot stop
                 %the running process!
                 pause(0.001);

                 %take care where to put this check codes.

        I1=readseq( readerobj,i );
        I2=readseq( readerobj,i+1 );

        I=I1-I2;

        for j=1:96 
            count=0;
            for locationx=(centrex(j)-radius):(centrex(j)+radius)
                for locationy=(centrey(j)-radius):(centrey(j)+radius)
                    if abs(I(locationy,locationx))>=thres
                        count=count+1;
                    end
                end
            end
            result_s(i,j)=count;
        end
    end  

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    
    %%%%%%%%%% batch processing function  end %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%       


    %first column of result
    frame_column(:,1) = 1:1:handles.nFrames-1;
    %second column of result
    time_stamp(:,1) = handles.duration_time/(handles.nFrames-0):handles.duration_time/(handles.nFrames-0):handles.duration_time;
    [a, ~]=size(time_stamp);
    time_stamp_temp=time_stamp(2:a,1); %caculate from the second


    %set current time as matrix's name
    %compose the output 
    result_output_s =[result_output_s frame_column time_stamp_temp result_s];

    %file name without extentions
    [~, name, ~] = fileparts(handles.file_list(k).name);
    handles.filename = name;

    %%output as CSV file
    csvwrite([handles.save_path,'\',handles.filename,'.csv'], result_output_s); %linux change 
end 
varargout{1} = 0;
end